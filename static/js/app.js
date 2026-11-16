const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const newChatBtn = document.getElementById("newChatBtn");

const sendButton = chatForm.querySelector("button[type='submit']");

let sessionId = null;
let isLoading = false;


// Ekrana mesaj ekle
function addMessage(role, content) {

    const welcome = document.querySelector(".welcome");

    if (welcome) {
        welcome.remove();
    }

    const messageDiv = document.createElement("div");

    messageDiv.className = `message ${role}`;

    messageDiv.textContent = content;

    messages.appendChild(messageDiv);

    messages.scrollTop = messages.scrollHeight;
}


// Yeni sohbet oluştur
async function createSession() {

    const response = await fetch("/sessions", {
        method: "POST"
    });

    if (!response.ok) {
    const errorData = await response.json();

    throw new Error(
        errorData.detail || "AI Agent yanıt vermedi."
    );
    }

    const data = await response.json();

    sessionId = data.session_id;

    messages.innerHTML = "";

    addMessage("assistant", "Merhaba! Size nasıl yardımcı olabilirim?");
    await loadSessions();
}


// Mesaj gönder
chatForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    if (isLoading) return;

    const message = messageInput.value.trim();

    if (!message) return;

    isLoading = true;
    sendButton.disabled = true;
    sendButton.textContent = "Bekleyin...";

    try {

        // Henüz sohbet oluşturulmadıysa oluştur
        if (!sessionId) {
            await createSession();
        }

        addMessage("user", message);

        messageInput.value = "";

        // FastAPI'ye mesaj gönder
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error("AI Agent yanıt vermedi.");
        }

        const data = await response.json();

        // Agent cevabını göster
        addMessage("assistant", data.answer);

        // Onay gerektiren işlem varsa şimdilik bilgi ver
        if (data.requires_confirmation && data.pending_action_id != null) {

            addConfirmationButtons(data.pending_action_id);

        }

    } catch (error) {

        console.error(error);

        addMessage("assistant", error.message);

    } finally {

        isLoading = false;
        sendButton.disabled = false;
        sendButton.textContent = "Gönder ➤";
    }
});


// Yeni Sohbet butonu
newChatBtn.addEventListener("click", async function () {

    if (isLoading) return;

    try {
        await createSession();
    } catch (error) {
        console.error(error);
        alert("Yeni sohbet oluşturulamadı.");
    }
});


function addConfirmationButtons(actionId) {

    const buttonsDiv = document.createElement("div");
    buttonsDiv.className = "confirmation-buttons";

    const approveBtn = document.createElement("button");
    approveBtn.textContent = "✅ Onayla";

    const cancelBtn = document.createElement("button");
    cancelBtn.textContent = "❌ İptal Et";

    approveBtn.className = "approve-btn";
    cancelBtn.className = "cancel-btn";

    buttonsDiv.appendChild(approveBtn);
    buttonsDiv.appendChild(cancelBtn);

    messages.appendChild(buttonsDiv);

    async function handleAction(actionType) {

        if (isLoading) return;

        isLoading = true;
        approveBtn.disabled = true;
        cancelBtn.disabled = true;
        sendButton.disabled = true;

        try {
            const response = await fetch(
                `/actions/${actionId}/${actionType}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        session_id: sessionId
                    })
                }
            );

            if (!response.ok) {
                throw new Error("İşlem gerçekleştirilemedi.");
            }

            const data = await response.json();

            buttonsDiv.remove();

            addMessage("assistant", data.answer);

        } catch (error) {

            console.error(error);

            addMessage(
                "assistant",
                "İşlem sırasında hata oluştu."
            );

            // İstek başarısız olursa tekrar denemeye izin ver.
            approveBtn.disabled = false;
            cancelBtn.disabled = false;

        } finally {
            isLoading = false;
            sendButton.disabled = false;
        }
    }

    approveBtn.addEventListener("click", function () {
        handleAction("approve");
    });

    cancelBtn.addEventListener("click", function () {
        handleAction("cancel");
    });
}


// PostgreSQL'deki sohbetleri sol menüde listele
async function loadSessions() {

    const response = await fetch("/sessions");

    if (!response.ok) {
        throw new Error("Sohbetler yüklenemedi.");
    }

    const data = await response.json();

    const chatList = document.getElementById("chatList");

    chatList.innerHTML = "";

    data.sessions.forEach(function (session) {

        const chatItem = document.createElement("button");

        chatItem.className = "chat-item";

        chatItem.dataset.sessionId = session.session_id;


        chatItem.textContent = "💬 " + session.title;
        chatItem.title = session.title;

        chatItem.addEventListener("click", function () {
            openSession(session.session_id);
        });

        chatList.appendChild(chatItem);
    });

    highlightActiveSession();
}



// Seçilen sohbetin geçmiş mesajlarını getir
async function openSession(selectedSessionId) {

    if (isLoading) return;

    try {
        // 1. Sohbet geçmişini getir
        const response = await fetch(
            `/sessions/${selectedSessionId}/messages`
        );

        if (!response.ok) {
            throw new Error("Sohbet geçmişi yüklenemedi.");
        }

        const data = await response.json();

        sessionId = selectedSessionId;

        highlightActiveSession();

        messages.innerHTML = "";

        // 2. Eski mesajları ekrana yaz
        data.messages.forEach(function (message) {
            addMessage(message.role, message.content);
        });

        // 3. Bekleyen onay işlemini kontrol et
        const pendingResponse = await fetch(
            `/sessions/${selectedSessionId}/pending-action`
        );

        if (!pendingResponse.ok) {
            throw new Error("Bekleyen işlem kontrol edilemedi.");
        }

        const pendingData = await pendingResponse.json();

        // 4. Bekleyen işlem varsa butonları göster
        if (pendingData.has_pending_action) {
            addConfirmationButtons(pendingData.pending_action_id);
        }

    } catch (error) {
        console.error(error);
        alert("Sohbet geçmişi açılamadı.");
    }
}



// Sayfa açıldığında sohbetleri listele
loadSessions().catch(function (error) {
    console.error("Sohbetler yüklenemedi:", error);
});

function highlightActiveSession() {
    const chatItems = document.querySelectorAll(".chat-item");

    chatItems.forEach(function (item) {
        const isActive = item.dataset.sessionId === sessionId;

        item.classList.toggle("active", isActive);
    });
}