import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerAddLabel(server: McpServer, api: TodoistApi) {
    server.tool(
        'add-label',
        'Add a label to a task in Todoist',
        {
            name: z.string(),
            color: z
                .enum([
                    'berry_red',
                    'light_blue',
                    'red',
                    'blue',
                    'orange',
                    'grape',
                    'yellow',
                    'violet',
                    'olive_green',
                    'lavender',
                    'lime_green',
                    'magenta',
                    'green',
                    'salmon',
                    'mint_green',
                    'charcoal',
                    'teal',
                    'grey',
                    'sky_blue',
                ])
                .optional(),
            isFavorite: z.boolean().optional(),
            order: z.number().optional(),
        },
        async ({ name, color, isFavorite, order }) => {
            const label = await api.addLabel({ name, color, isFavorite, order })
            return {
                content: [{ type: 'text', text: JSON.stringify(label, null, 2) }],
            }
        },
    )
}
