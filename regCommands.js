import { ApplicationCommandOptionType, REST, Routes } from "discord.js";
import dotenv from "dotenv";
import process from "node:process";

dotenv.config();

const commands = [
  {
    name: "jerry",
    description: "Ask Jeff a question",
    options: [
      {
        name: "message",
        description: "Message to sent to Jerry",
        type: ApplicationCommandOptionType.String,
        required: true,
      },
    ],
  },
  {
    name: "donate",
    description: "Donate to keep this bot up",
  },
];

const rest = new REST({ version: "10" }).setToken(process.env.DISCORD_TOKEN);

console.log("reg commands");
try {
  await rest.put(
    Routes.applicationGuildCommands(process.env.BOT_ID, process.env.BUILD_ID),
    {
      body: commands,
    },
  );
  console.log("commands regged");
} catch (err) {
  console.log(err);
}

// # https://discord.com/oauth2/authorize?client_id=1373548539459670027&permissions=0&scope=bot%20applications.commands
