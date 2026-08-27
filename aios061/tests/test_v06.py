from ai.llm_planner import LLMPlanner
from ai.object_planner import ObjectPlanner


class FakeClient:
    def generate(self, prompt: str) -> str:
        return "{\"action\":\"launch_app\",\"target_type\":\"application\",\"target\":\"chrome\",\"parameters\":{},\"risk\":\"low\",\"confidence\":0.93,\"explanation\":\"Open Chrome.\"}"


def test_local_llm_json_is_validated() -> None:
    intent = LLMPlanner(FakeClient()).plan("please open my browser")
    assert intent is not None
    assert intent.action == "launch_app"
    assert intent.parameters["app"] == "chrome"
    assert intent.confidence == 0.93


class BadClient:
    def generate(self, prompt: str) -> str:
        return "{\"action\":\"run_arbitrary_shell\",\"risk\":\"low\"}"


def test_llm_cannot_create_arbitrary_actions() -> None:
    assert LLMPlanner(BadClient()).plan("do anything") is None


def test_deterministic_planner_remains_fallback() -> None:
    intent = ObjectPlanner().plan("open downloads")
    assert intent is not None and intent.action == "open_path"
