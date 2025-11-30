import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerGetProject(server: McpServer, api: TodoistApi) {
    server.tool(
        'get-project',
        'Get a project from Todoist',
        { projectId: z.string() },
        async ({ projectId }) => {
            const project = await api.getProject(projectId)
            return {
                content: [{ type: 'text', text: JSON.stringify(project, null, 2) }],
            }
        },
    )
}
