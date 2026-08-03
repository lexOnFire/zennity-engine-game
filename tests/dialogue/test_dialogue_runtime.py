from engine.dialogue.runtime import DialogueSession


def dialogue():
    return {
        "format": "zennity.generic_graph",
        "category": "Dialogue",
        "nodes": [
            {"id": "hello", "type": "dialogue.speech", "inputs": {"speaker": "NPC", "text": "Olá"}},
            {"id": "choice", "type": "dialogue.choice", "inputs": {"prompt": "Abrir?"}},
            {"id": "condition", "type": "dialogue.condition", "inputs": {"condition_var": "key"}},
            {"id": "event", "type": "dialogue.event", "inputs": {"event_name": "open"}},
            {"id": "end", "type": "dialogue.end"},
        ],
        "edges": [
            {"source_node": "hello", "source_port": "out", "target_node": "choice"},
            {"source_node": "choice", "source_port": "option_1", "target_node": "condition"},
            {"source_node": "choice", "source_port": "option_2", "target_node": "end"},
            {"source_node": "condition", "source_port": "true", "target_node": "event"},
            {"source_node": "condition", "source_port": "false", "target_node": "end"},
            {"source_node": "event", "source_port": "out", "target_node": "end"},
        ],
    }


def test_dialogue_session_runs_speech_choice_condition_event_and_end():
    events = []
    session = DialogueSession(
        dialogue(), {"key": True},
        lambda name, payload: events.append((name, payload)),
    )
    assert session.start()["text"] == "Olá"
    assert session.advance()["options"] == [
        {"index": 1, "port": "option_1"},
        {"index": 2, "port": "option_2"},
    ]
    result = session.choose(1)
    assert result["finished"]
    assert events == [("open", None)]


def test_dialogue_choice_can_follow_cancel_branch():
    session = DialogueSession(dialogue())
    session.start()
    session.advance()
    assert session.choose("option_2")["finished"]
