import asyncio
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QWindow
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog
from dotenv import load_dotenv

from modules.config.models import Config
from modules.core.agent.agent import Agent
from modules.core.agent.models import (
    GeneratingFinished,
    GeneratingResponse,
    StreamingResponse,
)
from modules.errors import ProgramError
from modules.gui.app import MainWindow
from modules.gui.webcam_panel import State
from modules.utils.config import setup_logging
from modules.utils.qt_helper import clear_layout
from modules.utils.resource import get_resource_fullpath

_ = load_dotenv()
setup_logging()


def main():
    app = QApplication(sys.argv)

    style_sheet = get_resource_fullpath("css/style.qss")
    agent = Agent(config=Config().agent)
    if style_sheet:
        with open(style_sheet, "r") as style:
            app.setStyleSheet(style.read())

    window = MainWindow()
    window.show()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    window.chat_panel.user_msg_sent.connect(
        lambda text, image_urls: loop.create_task(
            _send_prompt(window, agent, text, image_urls)
        )
    )

    window.left_panel.save_session_clicked.connect(
        lambda path: loop.create_task(_save_session(agent, path))
    )

    window.left_panel.load_session_clicked.connect(
        lambda success, path: loop.create_task(
            _load_session(agent, window, success, path)
        )
    )

    timer = QTimer()
    timer.setInterval(10)

    def async_loop_step():
        loop.stop()
        loop.run_forever()

    timer.timeout.connect(async_loop_step)
    timer.start()

    try:
        sys.exit(app.exec())
    finally:
        loop.close()


async def _load_session(
    agent: Agent, window: MainWindow, success: bool, path: str
) -> None:
    if not success:
        return
    try:
        agent.load_session(path)

        if window.chat_panel.message_layout.children():
            clear_layout(window.chat_panel.message_layout)
        for message in agent._memory_manager.messages:
            if message["role"] == "tool" or message["role"] == "system":
                continue
            content = message.get("content")
            if not isinstance(content, str) or not content:
                continue
            is_user: bool = message["role"] == "user"
            text: str = content
            if is_user:
                text = text.split(":", 1)[1]

            window.chat_panel.add_message(text, is_user)

    except ProgramError as e:
        print(e.message)


async def _save_session(agent: Agent, path: str) -> None:
    print("SAVING")
    await agent.save_session(path)


async def _send_prompt(
    window: MainWindow, agent: Agent, text: str, image_urls: list[str]
) -> None:
    try:
        agent_response = agent.generate_response(
            "toffeezzz", text, Config().agent, image_urls or None
        )
        async for response in agent_response:
            if isinstance(response, GeneratingResponse):
                window.left_panel.webcam.change_state(State.TYPING)
                print("Generating.....")
            elif isinstance(response, StreamingResponse):
                if response.delta_content:
                    print(response.delta_content, end="")
            elif isinstance(response, GeneratingFinished):
                window.left_panel.webcam.change_state(State.IDLE)
                if response.content:
                    window.chat_panel.add_message(response.content)
        await agent.save_session("memory.json")

    except ProgramError as e:
        print(f"Error occured: {e.message}")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
