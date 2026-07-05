from app.clients.session_client import SessionData


class AgentState:
    """
    Wraps session data with read/write interface used by the rest of agent/.
    """

    def __init__(self, session: SessionData):
        self._session = session

    @property
    def user_id(self) -> str:
        return self._session.user_id

    @property
    def history(self) -> list[dict]:
        return self._session.history

    @history.setter
    def history(self, value: list[dict]) -> None:
        self._session.history = value

    @property
    def cart_draft(self) -> dict:
        return self._session.cart_draft

    @property
    def tool_log(self) -> list[dict]:
        return self._session.tool_log

    def append_to_history(self, entry: dict) -> None:
        self._session.history.append(entry)

    def append_to_tool_log(self, entry: dict) -> None:
        self._session.tool_log.append(entry)
