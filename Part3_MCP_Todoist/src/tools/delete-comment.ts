import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerDeleteComment(server: McpServer, api: TodoistApi) {
    server.tool(
        'delete-comment',
        'Delete a comment from a task in Todoist',
        {
            commentId: z.string(),
        },
        async ({ commentId }) => {
            const success = await api.deleteComment(commentId)
            return {
                content: [
                    {
                        type: 'text',
                        text: success
                            ? `Comment ${commentId} deleted`
                            : `Failed to delete comment ${commentId}`,
                    },
                ],
            }
        },
    )
}
