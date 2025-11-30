import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerGetComment(server: McpServer, api: TodoistApi) {
    server.tool(
        'get-comment',
        'Get a comment from a task or project in Todoist',
        { commentId: z.string() },
        async ({ commentId }) => {
            const comment = await api.getComment(commentId)
            return {
                content: [{ type: 'text', text: JSON.stringify(comment, null, 2) }],
            }
        },
    )
}
