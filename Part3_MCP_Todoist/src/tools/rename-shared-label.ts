import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerRenameSharedLabel(server: McpServer, api: TodoistApi) {
    server.tool(
        'rename-shared-label',
        'Rename a shared label in Todoist',
        { name: z.string(), newName: z.string() },
        async ({ name, newName }) => {
            const success = await api.renameSharedLabel({ name, newName })
            return {
                content: [
                    {
                        type: 'text',
                        text: success
                            ? `Shared label ${name} renamed to ${newName}`
                            : `Failed to rename shared label ${name} to ${newName}`,
                    },
                ],
            }
        },
    )
}
