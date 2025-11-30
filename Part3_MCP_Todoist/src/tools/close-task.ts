import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerCloseTask(server: McpServer, api: TodoistApi) {
    server.tool(
        'close-task',
        'Close (complete) a task in Todoist',
        {
            taskId: z.string(),
        },
        async ({ taskId }) => {
            const success = await api.closeTask(taskId)
            return {
                content: [
                    {
                        type: 'text',
                        text: success ? `Task ${taskId} closed` : `Failed to close task ${taskId}`,
                    },
                ],
            }
        },
    )
}
