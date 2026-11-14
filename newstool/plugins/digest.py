"""The `digest` applet (decision 0015) writes one digest of the stories its
sources covered over the last `span_days` whole local days. It filters the
items by their annotations, groups the items about the same story by tag
overlap (and, with `embeddings`, the similarity of their embeddings), ranks
the stories and has an LLM write an entry per chosen story from its items'
`input` text, plus an opening paragraph.

Each run emits a `plan` (JSON: the chosen stories, their scores and items)
and, with `write`, the `digest` (Markdown), both keyed `<from>_<to>`
(YYYY-MM-DD, the first and last day), so a second run over the same days
emits nothing new. Schedule it (`days`, `at`) for the period it covers."""

import dataclasses
import json
import logging
import math
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from itertools import combinations
from typing import ClassVar, Literal

import pydantic

from ..applets import (
    AppletReader,
    AppletType,
    BaseApplet,
    Outputs,
)
from ..config import Duration
from ..errors import PluginFailure
from ..llms import strip_code_fence
from ..models import AppletResult, AppletRun, EmittedDocument, SourceItem
from ..processors import embedding_key
from . import PluginTypes, Services, UsesLLMOptions

LOGGER = logging.getLogger(__name__)

PLAN_OUTPUT = "plan"
DIGEST_OUTPUT = "digest"

STORY_PROMPT = """You are the editor of a news digest. Below are the articles
that cover one story, each with its source, title, link and summary. Write
the story's entry in Markdown, in the same language as the articles:

- A `##` heading with the story's headline.
- A paragraph of 2 to 4 sentences.
- The links of the articles, as Markdown links titled with their source.
- Return only the entry.

Articles:

"""

INTRO_PROMPT = """You are the editor of a news digest. Below are its entries.
Write one opening paragraph that sums up the period, in the same language as
the entries. Return only the paragraph.

Entries:

"""

type Algorithm = Literal["singlelink", "avglink", "embeddings"]
type Matrix = list[list[float]]


class DigestOptions(UsesLLMOptions):
    title: str = "Digest"
    span_days: int = 7  # whole local days, ending yesterday
    input: str = "summary"  # the annotation each story is written from
    # Annotation key -> labels: an item is kept only with one of them...
    include: dict[str, list[str]] = pydantic.Field(default_factory=dict)
    # ...and dropped with any of these.
    exclude: dict[str, list[str]] = pydantic.Field(default_factory=dict)
    algorithm: Algorithm = "singlelink"
    min_score: float = 0.3
    tau: Duration | None = None  # time decay; None disables it
    embedding: str = "tags"  # the annotation `embed` embedded, for `embeddings`
    embedding_weight: float = 0.5
    # Topic (of the `topics` annotation) -> weight.
    topic_weights: dict[str, float] = pydantic.Field(default_factory=dict)
    source_weights: dict[str, float] = pydantic.Field(default_factory=dict)
    max_stories: int = 8
    write: bool = True  # False: emit only the plan
    story_prompt: str = STORY_PROMPT
    intro_prompt: str = INTRO_PROMPT
    model: str | None = None
    context_length: int = 32768  # the model's context window, in tokens


@dataclasses.dataclass(frozen=True, slots=True)
class Candidate:
    """An item to group, with what the grouping compares."""

    item: SourceItem
    text: str  # its `input` annotation
    tags: frozenset[str]  # lowercased
    topics: frozenset[str]
    vector: list[float] | None


@dataclasses.dataclass(frozen=True, slots=True)
class Story:
    members: tuple[Candidate, ...]
    score: float


class DigestApplet(BaseApplet):
    """Items without the `input` annotation are left out."""

    name = "digest"
    outputs: ClassVar[Outputs] = {
        PLAN_OUTPUT: frozenset({"application/json"}),
        DIGEST_OUTPUT: frozenset({"text/markdown"}),
    }
    options_model = DigestOptions
    options: DigestOptions

    def __init__(self, options: DigestOptions, services: Services) -> None:
        super().__init__(options, services)
        self.llm = services.llm(options.llm)

    @classmethod
    def required_keys(cls, options: DigestOptions) -> tuple[str, ...]:
        keys = [options.input, "tags", *options.include, *options.exclude]
        if options.topic_weights:
            keys.append("topics")
        if options.algorithm == "embeddings":
            keys.append(embedding_key(options.embedding))
        return tuple(dict.fromkeys(keys))

    def run(self, now: datetime, run: AppletRun, reader: AppletReader) -> AppletResult:
        options = self.options
        since, until = period(now, options.span_days)
        candidates = read_candidates(reader, options, since, until)
        stories = select_stories(candidates, options)
        if not stories:
            LOGGER.info(f"{self.name}: no stories in the period")
            return AppletResult()

        first_day, last_day = (
            f"{since:%Y-%m-%d}",
            f"{until - timedelta(days=1):%Y-%m-%d}",
        )
        key = f"{first_day}_{last_day}"
        title = f"{options.title}: {first_day} – {last_day}"
        documents = [
            EmittedDocument(
                output=PLAN_OUTPUT,
                key=key,
                content=json.dumps(
                    plan_payload(stories, len(candidates)), indent=2, ensure_ascii=False
                ),
                content_type="application/json",
                title=title,
            )
        ]
        if options.write:
            documents.append(
                EmittedDocument(
                    output=DIGEST_OUTPUT,
                    key=key,
                    content=self._write(title, stories),
                    content_type="text/markdown",
                    title=title,
                )
            )
        return AppletResult(documents=tuple(documents))

    def _write(self, title: str, stories: list[Story]) -> str:
        entries = [
            self._ask(self.options.story_prompt + story_text(story))
            for story in stories
        ]
        intro = self._ask(self.options.intro_prompt + "\n\n".join(entries))
        return f"# {title}\n\n{intro}\n\n" + "\n\n".join(entries) + "\n"

    def _ask(self, prompt: str) -> str:
        options = self.options
        response = self.llm.prompt(
            prompt, model=options.model, context_length=options.context_length
        )
        answer = strip_code_fence(response)
        if not answer:
            raise PluginFailure("LLM returned an empty answer")
        return answer


def period(now: datetime, span_days: int) -> tuple[datetime, datetime]:
    """The `span_days` whole local days before `now`'s day: [since, until)."""
    until = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    return until - timedelta(days=span_days), until


def read_candidates(
    reader: AppletReader, options: DigestOptions, since: datetime, until: datetime
) -> list[Candidate]:
    """The items of the period with `input` that pass the filters."""
    items = reader.items(published_since=since, published_until=until)
    texts = reader.annotations(items, options.input)
    items = [item for item in items if item.key in texts]
    filters = {
        key: reader.annotations(items, key)
        for key in (*options.include, *options.exclude)
    }
    items = [
        item
        for item in items
        if all(
            labels_of(filters[key].get(item.key)) & lowered(labels)
            for key, labels in options.include.items()
        )
        and not any(
            labels_of(filters[key].get(item.key)) & lowered(labels)
            for key, labels in options.exclude.items()
        )
    ]
    tags = reader.annotations(items, "tags")
    topics = reader.annotations(items, "topics") if options.topic_weights else {}
    vectors = (
        reader.annotations(items, embedding_key(options.embedding))
        if options.algorithm == "embeddings"
        else {}
    )
    return [
        Candidate(
            item=item,
            text=str(texts[item.key]),
            tags=labels_of(tags.get(item.key)),
            topics=labels_of(topics.get(item.key)),
            vector=as_vector(vectors.get(item.key)),
        )
        for item in items
    ]


def labels_of(value: object) -> frozenset[str]:
    """An annotation's labels, lowercased: a list's strings, or a string."""
    if isinstance(value, str):
        return frozenset({value.lower()})
    if isinstance(value, list):
        return lowered(label for label in value if isinstance(label, str))
    return frozenset()


def lowered(labels: Iterable[str]) -> frozenset[str]:
    return frozenset(label.lower() for label in labels)


def as_vector(value: object) -> list[float] | None:
    return value if isinstance(value, list) else None


def select_stories(candidates: list[Candidate], options: DigestOptions) -> list[Story]:
    """Group the candidates into stories and keep the `max_stories` best."""
    matrix = score_matrix(candidates, options)
    clusters = CLUSTERERS[options.algorithm](matrix, options.min_score)
    stories = [
        Story(
            members=tuple(
                sorted(
                    (candidates[index] for index in cluster),
                    key=lambda member: published_timestamp(member.item),
                )
            ),
            score=story_score([candidates[index] for index in cluster], options),
        )
        for cluster in clusters
    ]
    stories.sort(key=lambda story: (story.score, len(story.members)), reverse=True)
    return stories[: options.max_stories]


def published_timestamp(item: SourceItem) -> float:
    return item.published_at.timestamp() if item.published_at else 0.0


def story_score(members: list[Candidate], options: DigestOptions) -> float:
    """Distinct sources, plus the weights of the story's topics, plus the
    highest weight of its sources."""
    sources = {member.item.source.id for member in members}
    topics = frozenset().union(*(member.topics for member in members))
    weights = {topic.lower(): w for topic, w in options.topic_weights.items()}
    return (
        len(sources)
        + sum(weights.get(topic, 0.0) for topic in topics)
        + max(options.source_weights.get(source, 0.0) for source in sources)
    )


# Grouping, absorbed from the former `grouping` applets.


def score_matrix(candidates: list[Candidate], options: DigestOptions) -> Matrix:
    """The symmetric pairwise scores (diagonal unused)."""
    size = len(candidates)
    matrix = [[0.0] * size for _ in range(size)]
    for i, j in combinations(range(size), 2):
        matrix[i][j] = matrix[j][i] = pair_score(candidates[i], candidates[j], options)
    return matrix


def pair_score(a: Candidate, b: Candidate, options: DigestOptions) -> float:
    """Tag overlap, blended with the embeddings' cosine similarity when both
    have one, times the time decay with a `tau`."""
    score = jaccard(a.tags, b.tags)
    if a.vector is not None and b.vector is not None:
        cosine = max(cosine_similarity(a.vector, b.vector), 0.0)
        weight = options.embedding_weight
        score = weight * cosine + (1 - weight) * score
    if score == 0.0 or options.tau is None:
        return score
    return score * time_decay(a.item.published_at, b.item.published_at, options.tau)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def time_decay(a: datetime | None, b: datetime | None, tau: float) -> float:
    """exp(-delta/tau): 1.0 for simultaneous items, decaying towards 0 as the
    gap between publish times grows. Missing timestamps don't penalize."""
    if a is None or b is None:
        return 1.0
    return math.exp(-abs((a - b).total_seconds()) / tau)


def single_link_clusters(matrix: Matrix, min_score: float) -> list[list[int]]:
    """Connected components of the pairs scoring at least `min_score`.
    Transitive: one bridge item can chain two unrelated stories."""
    parent = list(range(len(matrix)))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for i, j in combinations(range(len(matrix)), 2):
        if matrix[i][j] >= min_score:
            parent[find(i)] = find(j)

    clusters: dict[int, list[int]] = {}
    for index in range(len(matrix)):
        clusters.setdefault(find(index), []).append(index)
    return list(clusters.values())


def average_link_clusters(matrix: Matrix, min_score: float) -> list[list[int]]:
    """Repeatedly merge the two clusters with the highest average score until
    it falls below `min_score`, so a bridge item can't chain stories. O(k^3)
    per merge, fine at tens of items."""
    clusters: list[list[int]] = [[i] for i in range(len(matrix))]
    while len(clusters) > 1:
        best, a, b = max(
            (average_between(clusters[a], clusters[b], matrix), a, b)
            for a, b in combinations(range(len(clusters)), 2)
        )
        if best < min_score:
            break
        merged = clusters[a] + clusters[b]
        clusters = [c for index, c in enumerate(clusters) if index not in (a, b)]
        clusters.append(merged)
    return clusters


def average_between(a: list[int], b: list[int], matrix: Matrix) -> float:
    scores = [matrix[i][j] for i in a for j in b]
    return sum(scores) / len(scores) if scores else 0.0


CLUSTERERS: dict[Algorithm, Callable[[Matrix, float], list[list[int]]]] = {
    "singlelink": single_link_clusters,
    "avglink": average_link_clusters,
    "embeddings": single_link_clusters,  # over scores blended with embeddings
}


def story_text(story: Story) -> str:
    return "\n\n".join(
        f"### {member.item.title}\n"
        f"Source: {member.item.source.name}\n"
        f"Link: {member.item.uri}\n\n"
        f"{member.text.strip()}"
        for member in story.members
    )


def plan_payload(stories: list[Story], candidates: int) -> dict[str, object]:
    return {
        "candidates": candidates,
        "stories": [
            {
                "score": story.score,
                "items": [
                    {
                        "source": member.item.source.id,
                        "title": member.item.title,
                        "link": member.item.uri,
                        "published_at": (
                            member.item.published_at.isoformat()
                            if member.item.published_at
                            else None
                        ),
                    }
                    for member in story.members
                ],
            }
            for story in stories
        ],
    }


def __newstool_plugin__() -> PluginTypes:
    return [(DigestApplet.name, AppletType, DigestApplet)]
