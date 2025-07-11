import logging
import os

import click

from agent import ReimbursementAgent
from common.server import A2AServer
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    MissingAPIKeyError,
)
from dotenv import load_dotenv
from task_manager import AgentTaskManager


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)
@click.option('--verify-signatures', is_flag=True, default=True, help='Enable signature verification')
def main(host, port, verify_signatures):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id='process_reimbursement',
            name='Process Reimbursement Tool',
            description='Helps with the reimbursement process for users given the amount and purpose of the reimbursement.',
            tags=['reimbursement'],
            examples=[
                'Can you reimburse me $20 for my lunch with the clients?'
            ],
        )
        agent_card = AgentCard(
            name='Reimbursement Agent',
            description='This agent handles the reimbursement process for the employees given the amount and purpose of the reimbursement.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        
        # Initialize the task manager with signature verification
        logger.info(f"Initializing AgentTaskManager with signature verification: {verify_signatures}")
        task_manager = AgentTaskManager(
            agent=ReimbursementAgent(),
            verify_signatures=verify_signatures
        )
        
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
