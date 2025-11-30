import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerDeleteTask(server: McpServer, api: TodoistApi) {
    server.tool(
        'delete-task',
        'Delete a task from a project in Todoist',
        { taskId: z.string() },
        async ({ taskId }) => {
            const success = await api.deleteTask(taskId)
            return {
                content: [
                    {
                        type: 'text',
                        text: success
                            ? `Task ${taskId} deleted`
                            : `Failed to delete task ${taskId}`,
                    },
                ],
            }
        },
    )
}
