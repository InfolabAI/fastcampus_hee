import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerGetTask(server: McpServer, api: TodoistApi) {
    server.tool(
        'get-task',
        'Retrieves a task by its ID in Todoist',
        {
            taskId: z.string(),
        },
        async ({ taskId }) => {
            const task = await api.getTask(taskId)
            return { content: [{ type: 'text', text: JSON.stringify(task, null, 2) }] }
        },
    )
}
