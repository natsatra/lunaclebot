export default {
  async fetch(request, env) {
    // Verify Telegram webhook secret
    const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (secret !== env.WEBHOOK_SECRET) {
      return new Response("Unauthorized", { status: 401 });
    }

    if (request.method !== "POST") {
      return new Response("OK", { status: 200 });
    }

    const CANNED_RESPONSES = {
      "thank": "You're welcome! 😊",
      "hi": "Hi there! 👋",
      "arigato": "You're welcome! :)",
      "nanni": "You're very welcome!",
      "hello": "Hello hello!",
      "hey": "Hey! 👋",
      "good morning": "Good morning! ☀️",
      "good night": "Good night! 🌙",
      "good evening": "Good evening!",
      "good afternoon": "Good afternoon!",
      "bye": "See ya!"
    };

    function findMatches(textLower) {
      const matched = [];
      for (const [trigger, response] of Object.entries(CANNED_RESPONSES)) {
        const pattern = new RegExp(`\\b${trigger.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
        if (pattern.test(textLower)) {
          matched.push(response);
        }
      }
      return matched;
    }

    async function sendMessage(botToken, chatId, text) {
      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, text: text })
      });
    }

    const body = await request.json();
    const message = body?.message;
    if (!message || !message.text) {
      return new Response("OK", { status: 200 });
    }

    const chatId = String(message.chat.id);
    const text = message.text;
    const textLower = text.toLowerCase().trim();
    const senderName = message.from?.first_name || "Someone";
    const myIds = env.MY_CHAT_IDS.split(",").map(id => id.trim());

    if (!myIds.includes(chatId)) {
      const matches = findMatches(textLower);
      if (matches.length > 0) {
        await sendMessage(env.BOT_TOKEN, chatId, matches.join(" "));
      } else {
        await sendMessage(env.BOT_TOKEN, chatId, "I can't hold conversations just yet, but I love your enthusiasm! 🌙");
      }

      for (const id of myIds) {
        await sendMessage(env.BOT_TOKEN, id, `📩 Message from ${senderName}:\n${text}`);
      }
    }

    return new Response("OK", { status: 200 });
  }
};
