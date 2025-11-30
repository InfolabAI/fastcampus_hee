import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerUpdateProject(server: McpServer, api: TodoistApi) {
    server.tool(
        'update-project',
        'Update a project in Todoist',
        {
            projectId: z.string(),
            name: z.string().optional(),
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
            viewStyle: z.enum(['list', 'board', 'calendar']).optional(),
        },
        async ({ projectId, name, color, isFavorite, viewStyle }) => {
            const project = await api.updateProject(projectId, {
                name,
                color,
                isFavorite,
                viewStyle,
            })
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify(project, null, 2),
                    },
                ],
            }
        },
    )
}
