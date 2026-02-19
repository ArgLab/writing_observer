//This setup uses model="gpt-3.5-turbo" & apiVersion="2023-05-15";

const { OpenAIClient, AzureKeyCredential } = require("@azure/openai");

const resource=await process.env.OPENAI_URL;
const deploymentID=process.env.OPENAI_DEPLOYMENT_ID;
const key = await process.env.OPENAI_API_KEY || 'EMPTY';

console.log("In azureInterface");
console.log("key: " + key);
const client = new OpenAIClient(resource, new AzureKeyCredential(key));
console.log("client created");

export async function listChatCompletions(
  messages,
  {
    maxTokens=128,
    temperature=0.8 // Currently ignored
  }) {
  console.log("azureInterface.listChatCompletions called");
  console.log(`Messages: ${messages.map((m) => m.content).join("\n")}`);
  console.log(client);
  const events = await client.getChatCompletions(deploymentID, messages, { maxTokens });
  return events.choices[0].message.content;
}
