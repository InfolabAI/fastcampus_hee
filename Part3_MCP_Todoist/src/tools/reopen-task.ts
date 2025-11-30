import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerReopenTask(server: McpServer, api: TodoistApi) {
    server.tool(
        'reopen-task',
        'Reopens a previously closed (completed) task in Todoist',
        { taskId: z.string() },
        async ({ taskId }) => {
            const success = await api.reopenTask(taskId)
            return {
                content: [
                    {
                        type: 'text',
                        text: success
                            ? `Task ${taskId} reopened`
                            : `Failed to reopen task ${taskId}`,
                    },
                ],
            }
        },
    )
}
