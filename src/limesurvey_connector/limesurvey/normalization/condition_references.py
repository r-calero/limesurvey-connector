"""Resolve imported identifiers without choosing between ambiguous aliases."""

import re
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

ConditionReference = tuple[str, str | None]


class UnsupportedConditionError(ValueError):
    """The source expression cannot be represented faithfully by the contract."""

    issue_code = "UNSUPPORTED_SOURCE_EXPRESSION"


class MissingConditionReferenceError(UnsupportedConditionError):
    """The expression names a question or response absent from this survey."""

    issue_code = "MISSING_CONDITION_REFERENCE"


class ConditionReferenceIndex(dict[str, ConditionReference]):
    """Temporary import index; ambiguous names are never usable references."""

    def __init__(self) -> None:
        super().__init__()
        self.ambiguous_aliases: set[str] = set()
        self.questions: dict[str, dict[str, Any]] = {}
        self.response_items: dict[str, list[str]] = {}

    def add(self, alias: str, target: ConditionReference) -> None:
        # A derived response alias must not shadow an explicit question code.
        if target[1] is not None and alias in self.questions:
            return
        if not alias or alias in self.ambiguous_aliases:
            return
        if alias in self and self[alias] != target:
            del self[alias]
            self.ambiguous_aliases.add(alias)
        else:
            self[alias] = target


def build_condition_references(
    questions: list[dict[str, Any]], survey_id: str
) -> ConditionReferenceIndex:
    """Index codes, qid, Q<qid>, SGQA and actual parent/child relationships once."""
    result = ConditionReferenceIndex()
    parents = []
    children = defaultdict(list)
    for question in questions:
        parent_id = str(question.get("parent_qid") or "0").strip()
        if parent_id in {"", "0"}:
            parents.append(question)
            code = str(question.get("title") or "").strip()
            if code:
                result.questions[code] = question
        else:
            children[parent_id].append(question)
    for question in parents:
        qid = str(question.get("qid") or "").strip()
        code = str(question.get("title") or "").strip()
        gid = str(question.get("gid") or "").strip()
        if not code:
            continue
        tokens = {code}
        if qid:
            tokens.update((qid, f"Q{qid}"))
        if survey_id and gid and qid:
            tokens.add(f"{survey_id}X{gid}X{qid}")
        for token in tokens:
            result.add(token, (code, None))
        native = question.get("type")
        question_children = children[qid]
        if native in {":", ";", "1"}:
            rows = [
                child for child in question_children if str(child.get("scale_id") or "0") == "0"
            ]
            columns = (
                [{"title": str(scale)} for scale in (0, 1)]
                if native == "1"
                else [child for child in question_children if str(child.get("scale_id")) == "1"]
            )
            result.response_items[code] = []
            for row in rows:
                for column in columns:
                    row_code, column_code = (
                        str(row.get("title") or "").strip(),
                        str(column.get("title") or "").strip(),
                    )
                    if not row_code or not column_code:
                        continue
                    item_code = f"{row_code}_{column_code}"
                    result.response_items[code].append(item_code)
                    for token in tokens:
                        result.add(f"{token}_{item_code}", (code, item_code))
                        result.add(f"{token}{item_code}", (code, item_code))
                        if native == "1":
                            result.add(f"{token}{row_code}#{column_code}", (code, item_code))
                            result.add(f"{token}_{row_code}#{column_code}", (code, item_code))
            continue
        result.response_items[code] = []
        for child in children[qid]:
            item_code = str(child.get("title") or "").strip()
            child_qid = str(child.get("qid") or "").strip()
            if not item_code:
                continue
            result.response_items[code].append(item_code)
            for token in tokens:
                result.add(f"{token}_{item_code}", (code, item_code))
                result.add(f"{token}{item_code}", (code, item_code))
            if child_qid:
                result.add(f"Q{qid}_S{child_qid}", (code, item_code))
    return result


def resolve_reference(raw: str, references: Mapping[str, ConditionReference]) -> ConditionReference:
    token = re.sub(r"\.(NAOK|code)$", "", raw.strip(), flags=re.IGNORECASE)
    if isinstance(references, ConditionReferenceIndex) and token in references.ambiguous_aliases:
        raise UnsupportedConditionError(
            f'LimeSurvey condition alias "{token}" identifies more than one imported response. '
            "The condition was omitted; use an unambiguous question code in LimeSurvey."
        )
    if token in references:
        return references[token]
    raise MissingConditionReferenceError(
        f'LimeSurvey condition reference "{token}" could not be matched to any '
        "imported question or subquestion. The condition was omitted."
    )
