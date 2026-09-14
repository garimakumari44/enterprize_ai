import { z } from "zod";

export const AgentSchema = z.object({
  id: z.string(),

  name: z.string(),

  description: z.string(),

  systemPrompt: z.string(),

  tools: z.array(z.string()),
});