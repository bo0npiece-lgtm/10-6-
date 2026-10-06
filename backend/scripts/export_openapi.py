"""OpenAPI(Swagger) 스펙을 docs/openapi.json 으로 내보내고, README 의 API 문서 섹션을 다시 생성한다.

사용법 (backend 폴더에서):
    python scripts/export_openapi.py

API 를 추가/변경했다면 다시 실행하면 된다. README 의
<!-- API_DOCS_START --> ~ <!-- API_DOCS_END --> 사이만 교체된다.
"""
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402

SPEC_PATH = ROOT / "docs" / "openapi.json"
README_PATH = ROOT / "README.md"
START, END = "<!-- API_DOCS_START -->", "<!-- API_DOCS_END -->"
REPO_RAW = "https://raw.githubusercontent.com/bo0npiece-lgtm/10-6-/main/docs/openapi.json"
METHOD_ORDER = ["get", "post", "patch", "put", "delete"]

# 스키마에 examples 가 없는 문자열 필드는 필드 이름으로 예시 값을 채운다 (시드 데이터 기준)
STRING_HINTS = {
    "nickname": "민수",
    "title": "알고리즘 스터디",
    "study_title": "알고리즘 스터디",
    "description": "주 2회 백준 문제 풀이",
    "message": "참여하고 싶어요!",
    "name": "A룸 (소형)",
    "detail": "방장만 할 수 있는 작업입니다.",
}


def resolve(spec, schema):
    while "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        schema = spec["components"]["schemas"][name]
    return schema


def example(spec, schema, depth=0, key=None):
    """스키마에서 예시 값을 만든다 (examples → enum → 필드 이름 힌트 → 타입 기본값 순)."""
    schema = resolve(spec, schema)
    if "examples" in schema:
        return schema["examples"][0]
    if "default" in schema and schema["default"] is not None:
        return schema["default"]
    if "anyOf" in schema:
        non_null = [s for s in schema["anyOf"] if s.get("type") != "null"]
        return example(spec, non_null[0], depth, key) if non_null else None
    if "allOf" in schema:
        return example(spec, schema["allOf"][0], depth)
    if "enum" in schema:
        return schema["enum"][0]
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        if depth > 4:
            return {}
        return {k: example(spec, v, depth + 1, k) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        return [example(spec, schema.get("items", {}), depth + 1)]
    if t == "integer":
        return 1
    if t == "number":
        return 1.0
    if t == "boolean":
        return True
    if t == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            return "2026-10-07T16:00:00" if key == "end_at" else "2026-10-07T14:00:00"
        if fmt == "date":
            return "2026-10-07"
        return STRING_HINTS.get(key, "string")
    return None


def type_name(spec, schema):
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        target = spec["components"]["schemas"][name]
        return " \\| ".join(target["enum"]) if "enum" in target else name
    if "anyOf" in schema:
        return " \\| ".join(type_name(spec, s) for s in schema["anyOf"])
    if schema.get("type") == "array":
        return f"{type_name(spec, schema.get('items', {}))}[]"
    return schema.get("format") or schema.get("type", "any")


def code_block(obj):
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


def render_endpoint(spec, path, method, op):
    lines = [f"<details>\n<summary><code>{method.upper()} {path}</code> {op.get('summary', '')}</summary>\n"]
    if op.get("description"):
        lines.append(op["description"].strip().replace("\n", "  \n") + "\n")

    params = op.get("parameters", [])
    if params:
        lines.append("**파라미터**\n")
        lines.append("| 이름 | 위치 | 타입 | 필수 | 설명 |")
        lines.append("|---|---|---|---|---|")
        for p in params:
            req = "✅" if p.get("required") else ""
            lines.append(
                f"| `{p['name']}` | {p['in']} | {type_name(spec, p['schema'])} | {req} | {p.get('description', '')} |"
            )
        lines.append("")

    body = op.get("requestBody", {}).get("content", {}).get("application/json")
    if body:
        lines.append("**요청 body**\n")
        lines.append(code_block(example(spec, body["schema"])) + "\n")

    lines.append("**응답**\n")
    lines.append("| 코드 | 설명 |")
    lines.append("|---|---|")
    ok_example = None
    for code, resp in sorted(op.get("responses", {}).items()):
        desc = {
            "422": "요청 형식 오류 (FastAPI 자동 검증)",
        }.get(code) or ("성공" if code.startswith("2") else resp.get("description", ""))
        lines.append(f"| {code} | {desc} |")
        content = resp.get("content", {}).get("application/json")
        if code.startswith("2") and content and content.get("schema"):
            ok_example = example(spec, content["schema"])
    lines.append("")
    if ok_example not in (None, {}):
        lines.append("<sub>성공 응답 예시</sub>\n")
        lines.append(code_block(ok_example) + "\n")
    lines.append("</details>\n")
    return "\n".join(lines)


def render(spec):
    tags = {t["name"]: t.get("description", "") for t in spec.get("tags", [])}
    groups = {name: [] for name in tags}
    for path, item in spec["paths"].items():
        for method in METHOD_ORDER:
            if method in item:
                op = item[method]
                groups.setdefault(op.get("tags", ["etc"])[0], []).append((path, method, op))

    out = [
        START,
        "<!-- 이 섹션은 backend/scripts/export_openapi.py 로 자동 생성됩니다. 직접 수정하지 마세요. -->",
        "",
        f"- **Swagger UI (로컬):** 백엔드 실행 후 http://localhost:8000/docs (ReDoc: http://localhost:8000/redoc)",
        f"- **Swagger UI (온라인):** [petstore.swagger.io에서 보기](https://petstore.swagger.io/?url={REPO_RAW})",
        "- **OpenAPI 스펙 파일:** [docs/openapi.json](docs/openapi.json) (Postman, Insomnia 등에서 import 가능)",
        "- **재생성:** `cd backend && python scripts/export_openapi.py`",
        "",
        "### 엔드포인트 요약",
        "",
        "| 메서드 | 경로 | 설명 |",
        "|---|---|---|",
    ]
    for name, ops in groups.items():
        for path, method, op in ops:
            out.append(f"| `{method.upper()}` | `{path}` | {op.get('summary', '')} |")
    out.append("")
    out.append("### 상세")
    out.append("")
    out.append("각 항목을 클릭하면 파라미터, 요청 body 예시, 응답 코드가 펼쳐집니다.")
    out.append("")
    for name, ops in groups.items():
        if not ops:
            continue
        out.append(f"#### {name}: {tags.get(name, '')}\n")
        for path, method, op in ops:
            out.append(render_endpoint(spec, path, method, op))
    out.append(END)
    return "\n".join(out)


def main():
    spec = app.openapi()
    SPEC_PATH.parent.mkdir(exist_ok=True)
    SPEC_PATH.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OpenAPI 스펙 저장: {SPEC_PATH.relative_to(ROOT)}")

    readme = README_PATH.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        sys.exit(f"README 에 {START} / {END} 표시가 없습니다.")
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    README_PATH.write_text(head + render(spec) + tail, encoding="utf-8")
    print(f"README API 문서 갱신: {README_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
