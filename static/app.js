let currentUser = null;
let currentHub = null;
let currentChannel = null;
let selectedHubColor = "#7c5cff";
let replyMessageId = null;
let messageRefreshTimer = null;


/* =========================================================
   BASIC
========================================================= */

function $(id) {
    return document.getElementById(id);
}


function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function showToast(
    message,
    type = "info"
) {

    const container =
        $("toastContainer");

    const toast =
        document.createElement("div");

    toast.className =
        "toast " + type;

    toast.textContent =
        message;

    container.appendChild(
        toast
    );

    setTimeout(
        () => {
            toast.remove();
        },
        3500
    );
}


async function api(
    url,
    options = {}
) {

    try {

        const response =
            await fetch(
                url,
                options
            );

        const data =
            await response.json();

        if (
            response.status === 401
        ) {

            showAuth("login");

            $("authScreen")
                .classList.remove("hidden");

            $("app")
                .classList.add("hidden");

        }

        return data;

    } catch (error) {

        showToast(
            "Verbindung zu HUB fehlgeschlagen.",
            "error"
        );

        return {
            success: false,
            error:
                "Verbindungsfehler."
        };
    }
}


/* =========================================================
   AUTH
========================================================= */

function showAuth(
    mode
) {

    document
        .querySelectorAll(".auth-tab")
        .forEach(
            button => {

                button.classList.toggle(
                    "active",
                    button.dataset.auth === mode
                );

            }
        );

    $("loginForm")
        .classList.toggle(
            "hidden",
            mode !== "login"
        );

    $("registerForm")
        .classList.toggle(
            "hidden",
            mode !== "register"
        );
}


async function checkLogin() {

    const data =
        await api(
            "/api/me"
        );

    if (
        data.logged_in
    ) {

        currentUser =
            data.user;

        startApp();

    } else {

        $("authScreen")
            .classList.remove("hidden");

        $("app")
            .classList.add("hidden");

    }
}


async function login() {

    const username =
        $("loginUsername")
            .value
            .trim();

    const password =
        $("loginPassword")
            .value;

    $("loginError")
        .textContent = "";

    if (!username || !password) {

        $("loginError")
            .textContent =
                "Bitte fülle beide Felder aus.";

        return;
    }

    const data =
        await api(
            "/api/login",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    username,
                    password
                })
            }
        );

    if (!data.success) {

        $("loginError")
            .textContent =
                data.error;

        return;
    }

    await checkLogin();
}


async function register() {

    const username =
        $("registerUsername")
            .value
            .trim();

    const password =
        $("registerPassword")
            .value;

    const password2 =
        $("registerPassword2")
            .value;

    $("registerError")
        .textContent = "";

    if (
        !username ||
        !password ||
        !password2
    ) {

        $("registerError")
            .textContent =
                "Bitte fülle alle Felder aus.";

        return;
    }

    if (
        password !== password2
    ) {

        $("registerError")
            .textContent =
                "Die Passwörter stimmen nicht überein.";

        return;
    }

    const data =
        await api(
            "/api/register",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    username,
                    password
                })
            }
        );

    if (!data.success) {

        $("registerError")
            .textContent =
                data.error;

        return;
    }

    await checkLogin();
}


async function logout() {

    await api(
        "/api/logout",
        {
            method: "POST"
        }
    );

    location.reload();
}


/* =========================================================
   START APP
========================================================= */

async function startApp() {

    $("authScreen")
        .classList.add("hidden");

    $("app")
        .classList.remove("hidden");

    updateUserUI();

    applyUserSettings();

    await loadHubs();

    await loadNotifications();

    showHome();
}


function updateUserUI() {

    if (!currentUser) {
        return;
    }

    const username =
        currentUser.username;

    const initial =
        username
            .charAt(0)
            .toUpperCase();

    $("profileName")
        .textContent = username;

    $("topUsername")
        .textContent = username;

    $("profileAvatar")
        .textContent = initial;

    $("topAvatar")
        .textContent = initial;

    $("largeProfileAvatar")
        .textContent = initial;

    $("largeProfileName")
        .textContent = username;

    $("largeProfileBio")
        .textContent =
            currentUser.bio ||
            "HUB member";

    $("settingsUsername")
        .value = username;

    $("settingsBio")
        .value =
            currentUser.bio || "";
}


function applyUserSettings() {

    if (!currentUser) {
        return;
    }

    document.body
        .classList.toggle(
            "light",
            currentUser.theme === "light"
        );

    document.body
        .classList.toggle(
            "compact",
            Boolean(
                currentUser.compact_mode
            )
        );
}


/* =========================================================
   HOME
========================================================= */

function hideAllPages() {

    document
        .querySelectorAll(".page")
        .forEach(
            page => {
                page.classList.add(
                    "hidden"
                );
            }
        );
}


function showHome() {

    hideAllPages();

    $("homePage")
        .classList.remove("hidden");

    $("topbarTitle")
        .textContent = "Home";

    loadHomeActivity();
}


async function loadHomeActivity() {

    const container =
        $("homeActivity");

    container.innerHTML =
        `
        <div class="activity-item">
            <div class="avatar">H</div>
            <div>
                <p>Welcome to HUB.</p>
                <small>Your workspace is ready.</small>
            </div>
        </div>
        `;

    const data =
        await api(
            "/hubs"
        );

    if (
        !data.hubs ||
        data.hubs.length === 0
    ) {

        container.innerHTML =
            `
            <div class="data-card">
                <h3>No Hubs yet</h3>
                <p>
                    Create your first Hub to start building your workspace.
                </p>
            </div>
            `;

        return;
    }

    let html = "";

    for (
        const hub of data.hubs.slice(0, 5)
    ) {

        html +=
            `
            <div class="activity-item">

                <div
                    class="hub-icon"
                    style="
                        background:${hub.color}22;
                        color:${hub.color};
                    "
                >
                    ${hub.icon_type === "image"
                        ? `<img src="${escapeHtml(hub.icon)}">`
                        : escapeHtml(hub.icon)}
                </div>

                <div>

                    <p>
                        <strong>
                            ${escapeHtml(hub.name)}
                        </strong>
                        is part of your workspace.
                    </p>

                    <small>
                        ${escapeHtml(
                            hub.description ||
                            "Your HUB"
                        )}
                    </small>

                </div>

            </div>
            `;
    }

    container.innerHTML = html;
}


/* =========================================================
   HUB LIST
========================================================= */

async function loadHubs() {

    const data =
        await api(
            "/hubs"
        );

    const list =
        $("hubList");

    list.innerHTML = "";

    if (
        !data.hubs ||
        data.hubs.length === 0
    ) {

        list.innerHTML =
            `
            <div class="empty-hubs">
                No Hubs yet
            </div>
            `;

        return;
    }

    data.hubs.forEach(
        hub => {

            const button =
                document.createElement(
                    "button"
                );

            button.className =
                "hub-item";

            button.onclick =
                () => openHub(
                    hub.id
                );

            const icon =
                document.createElement(
                    "div"
                );

            icon.className =
                "hub-icon";

            icon.style.background =
                hub.color + "22";

            icon.style.color =
                hub.color;

            if (
                hub.icon_type === "image"
            ) {

                icon.innerHTML =
                    `
                    <img
                        src="${escapeHtml(hub.icon)}"
                        alt=""
                    >
                    `;

            } else {

                icon.textContent =
                    hub.icon;

            }

            const name =
                document.createElement(
                    "span"
                );

            name.textContent =
                hub.name;

            button.appendChild(
                icon
            );

            button.appendChild(
                name
            );

            list.appendChild(
                button
            );

        }
    );
}


/* =========================================================
   CREATE HUB
========================================================= */

function openCreateHub() {

    $("createHubModal")
        .classList.remove("hidden");

    $("hubName")
        .focus();
}


function selectHubColor(
    element
) {

    selectedHubColor =
        element.dataset.color;

    document
        .querySelectorAll(
            ".color-option"
        )
        .forEach(
            item => {
                item.classList.remove(
                    "selected"
                );
            }
        );

    element.classList.add(
        "selected"
    );

    $("hubIconPreview")
        .style.background =
            selectedHubColor;
}


function previewHubIcon(
    event
) {

    const file =
        event.target.files[0];

    if (!file) {
        return;
    }

    const reader =
        new FileReader();

    reader.onload =
        function () {

            $("hubIconPreview")
                .innerHTML =
                    `
                    <img
                        src="${reader.result}"
                        alt=""
                    >
                    `;

        };

    reader.readAsDataURL(
        file
    );
}


const hubNameInput = $("hubName");

if (hubNameInput) {
    hubNameInput.addEventListener(
        "input",
        function () {

            const hubIconFile = $("hubIconFile");
            const hubIconPreview = $("hubIconPreview");

            if (
                hubIconFile &&
                hubIconPreview &&
                !hubIconFile.files.length
            ) {

                const value =
                    this.value.trim();

                hubIconPreview.textContent =
                    value
                        ? value.charAt(0).toUpperCase()
                        : "H";
            }
        }
    );
}


async function createHub() {

    const name =
        $("hubName")
            .value
            .trim();

    const description =
        $("hubDescription")
            .value
            .trim();

    $("createHubError")
        .textContent = "";

    if (!name) {

        $("createHubError")
            .textContent =
                "Bitte gib einen Namen ein.";

        return;
    }

    const formData =
        new FormData();

    formData.append(
        "name",
        name
    );

    formData.append(
        "description",
        description
    );

    formData.append(
        "color",
        selectedHubColor
    );

    formData.append(
        "public",
        $("hubPublic").checked
            ? "1"
            : "0"
    );

    formData.append(
        "rules",
        $("hubRules")
            .value
            .trim()
    );

    const file =
        $("hubIconFile")
            .files[0];

    if (file) {

        formData.append(
            "icon_file",
            file
        );

    }

    const data =
        await api(
            "/api/hubs/create",
            {
                method: "POST",
                body: formData
            }
        );

    if (!data.success) {

        $("createHubError")
            .textContent =
                data.error;

        return;
    }

    closeModal(
        "createHubModal"
    );

    $("hubName").value = "";
    $("hubDescription").value = "";
    $("hubRules").value = "";
    $("hubIconFile").value = "";
    $("hubPublic").checked = false;

    $("hubIconPreview")
        .innerHTML = "H";

    showToast(
        "Hub wurde erstellt.",
        "success"
    );

    await loadHubs();

    openHub(
        data.hub_id
    );
}


/* =========================================================
   OPEN HUB
========================================================= */

async function openHub(
    hubId
) {

    const data =
        await api(
            `/api/hubs/${hubId}`
        );

    if (!data.success) {

        showToast(
            data.error ||
            "Hub konnte nicht geöffnet werden.",
            "error"
        );

        return;
    }

    currentHub =
        data.hub;

    currentHub.members =
        data.members;

    currentHub.channels =
        data.channels;

    hideAllPages();

    $("hubPage")
        .classList.remove(
            "hidden"
        );

    $("topbarTitle")
        .textContent =
            currentHub.name;

    renderHubHeader();

    renderChannels();

    if (
        currentHub.channels.length
    ) {

        currentChannel =
            currentHub.channels[0];

        await loadMessages();

    }

    showHubTab(
        "chat"
    );
}


function renderHubHeader() {

    const icon =
        currentHub.icon_type === "image"
            ? `
                <img
                    src="${escapeHtml(currentHub.icon)}"
                    alt=""
                >
              `
            : escapeHtml(
                currentHub.icon
            );

    $("hubHeader")
        .innerHTML =
        `
        <div class="hub-header-inner">

            <div
                class="hub-large-icon"
                style="
                    background:${currentHub.color}22;
                    color:${currentHub.color};
                "
            >
                ${icon}
            </div>

            <div>

                <h1>
                    ${escapeHtml(
                        currentHub.name
                    )}
                </h1>

                <p>
                    ${escapeHtml(
                        currentHub.description ||
                        "No description"
                    )}
                </p>

            </div>

            <div class="hub-header-actions">

                <button
                    class="secondary-button"
                    onclick="createInviteLink()"
                >
                    Invite
                </button>

                ${
                    currentHub.owner_id === currentUser.id
                    ? `
                    <button
                        class="danger-button"
                        onclick="confirmDeleteHub()"
                    >
                        Delete
                    </button>
                    `
                    : ""
                }

            </div>

        </div>
        `;
}


function renderChannels() {

    const container =
        $("channelSidebar");

    let html =
        `
        <div class="channel-label">
            CHANNELS
        </div>
        `;

    currentHub.channels.forEach(
        channel => {

            html +=
                `
                <button
                    class="channel-item ${
                        currentChannel &&
                        currentChannel.id === channel.id
                            ? "active"
                            : ""
                    }"
                    onclick="selectChannel(${channel.id})"
                >
                    <span>${
                        channel.channel_type === "announcement"
                            ? "!"
                            : "#"
                    }</span>
                    ${escapeHtml(
                        channel.name
                    )}
                </button>
                `;

        }
    );

    if (
        currentHub.role === "owner" ||
        currentHub.role === "admin"
    ) {

        html +=
            `
            <button
                class="channel-item"
                onclick="openCreateChannel()"
            >
                <span>+</span>
                Add channel
            </button>
            `;

    }

    container.innerHTML =
        html;
}


async function selectChannel(
    channelId
) {

    currentChannel =
        currentHub.channels
            .find(
                channel =>
                    channel.id === channelId
            );

    renderChannels();

    await loadMessages();

    showHubTab(
        "chat"
    );
}


/* =========================================================
   CHAT
========================================================= */

async function loadMessages() {

    if (!currentChannel) {
        return;
    }

    const data =
        await api(
            `/api/channels/${currentChannel.id}/messages`
        );

    const list =
        $("messageList");

    if (
        !data.messages ||
        data.messages.length === 0
    ) {

        list.innerHTML =
            `
            <div class="data-card">
                <h3>
                    #${escapeHtml(
                        currentChannel.name
                    )}
                </h3>

                <p>
                    No messages yet. Start the conversation.
                </p>
            </div>
            `;

        return;
    }

    list.innerHTML =
        data.messages
            .map(
                renderMessage
            )
            .join("");

    list.scrollTop =
        list.scrollHeight;
}


function renderMessage(
    message
) {

    const initial =
        message.username
            .charAt(0)
            .toUpperCase();

    let reactions =
        "";

    if (
        message.reactions &&
        message.reactions.length
    ) {

        reactions =
            `
            <div class="reactions">

                ${
                    message.reactions
                        .map(
                            reaction =>
                                `
                                <button
                                    class="reaction"
                                    onclick="reactToMessage(
                                        ${message.id},
                                        '${escapeHtml(
                                            reaction.emoji
                                        )}'
                                    )"
                                >
                                    ${escapeHtml(
                                        reaction.emoji
                                    )}
                                    ${reaction.count}
                                </button>
                                `
                        )
                        .join("")
                }

            </div>
            `;

    }

    return `
        <article
            class="message ${
                message.edited
                    ? "edited"
                    : ""
            }"
        >

            <div class="message-avatar">

                <div class="avatar">
                    ${escapeHtml(
                        initial
                    )}
                </div>

            </div>

            <div class="message-body">

                <div class="message-meta">

                    <strong>
                        ${escapeHtml(
                            message.username
                        )}
                    </strong>

                    <small>
                        ${formatDate(
                            message.created_at
                        )}
                    </small>

                    ${
                        message.pinned
                        ? "<small>📌</small>"
                        : ""
                    }

                </div>

                ${
                    message.reply_to
                    ? `
                    <div class="reply-reference">
                        Reply
                    </div>
                    `
                    : ""
                }

                <div class="message-content">
                    ${escapeHtml(
                        message.content
                    )}
                </div>

                ${reactions}

            </div>


            <div class="message-actions">

                ${
                    message.user_id === currentUser.id
                    ? `
                    <button
                        onclick="editMessage(${message.id})"
                        title="Edit"
                    >
                        ✎
                    </button>
                    `
                    : ""
                }

                <button
                    onclick="replyToMessage(${message.id})"
                    title="Reply"
                >
                    ↩
                </button>

                <button
                    onclick="reactToMessage(${message.id}, '❤️')"
                    title="React"
                >
                    ♡
                </button>

                ${
                    message.user_id === currentUser.id ||
                    ["owner","admin","moderator"].includes(
                        getCurrentHubRole()
                    )
                    ? `
                    <button
                        class="delete"
                        onclick="deleteMessage(${message.id})"
                        title="Delete"
                    >
                        🗑
                    </button>
                    `
                    : ""
                }

                ${
                    ["owner","admin","moderator"].includes(
                        getCurrentHubRole()
                    )
                    ? `
                    <button
                        onclick="pinMessage(${message.id})"
                        title="Pin"
                    >
                        📌
                    </button>
                    `
                    : ""
                }

            </div>

        </article>
    `;
}


function getCurrentHubRole() {

    if (!currentHub) {
        return "member";
    }

    const member =
        currentHub.members
            .find(
                item =>
                    item.user_id === currentUser.id
            );

    return member
        ? member.role
        : "member";
}


async function sendCurrentMessage() {

    if (!currentChannel) {
        return;
    }

    if (
        currentChannel.channel_type === "announcement" &&
        !["owner", "admin"].includes(
            getCurrentHubRole()
        )
    ) {
        showToast(
            "Nur Owner und Admins können in Announcements posten.",
            "error"
        );
        return;
    }

    const input =
        $("messageInput");

    const content =
        input.value.trim();

    if (!content) {
        return;
    }

    const data =
        await api(
            `/api/channels/${currentChannel.id}/messages`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    content,
                    reply_to:
                        replyMessageId
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error ||
            "Nachricht konnte nicht gesendet werden.",
            "error"
        );

        return;
    }

    input.value = "";

    cancelReply();

    await loadMessages();
}


function messageKeydown(
    event
) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendCurrentMessage();
    }
}


async function deleteMessage(
    messageId
) {

    openConfirm(
        "Nachricht löschen",
        "Diese Nachricht wird dauerhaft gelöscht.",
        async function () {

            const data =
                await api(
                    `/api/messages/${messageId}`,
                    {
                        method: "DELETE"
                    }
                );

            if (!data.success) {

                showToast(
                    data.error ||
                    "Nachricht konnte nicht gelöscht werden.",
                    "error"
                );

                return;
            }

            showToast(
                "Nachricht gelöscht.",
                "success"
            );

            await loadMessages();

        }
    );
}


async function editMessage(
    messageId
) {

    const message =
        promptMessageInput(
            "Neue Nachricht"
        );

    if (
        message === null
    ) {
        return;
    }

    if (!message.trim()) {
        return;
    }

    const data =
        await api(
            `/api/messages/${messageId}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    content:
                        message.trim()
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error ||
            "Nachricht konnte nicht bearbeitet werden.",
            "error"
        );

        return;
    }

    await loadMessages();
}


function promptMessageInput(
    title
) {

    return window.prompt(
        title
    );
}


function replyToMessage(
    messageId
) {

    replyMessageId =
        messageId;

    $("replyBar")
        .classList.remove(
            "hidden"
        );

    $("messageInput")
        .focus();
}


function cancelReply() {

    replyMessageId =
        null;

    $("replyBar")
        .classList.add(
            "hidden"
        );
}


async function reactToMessage(
    messageId,
    emoji
) {

    await api(
        `/api/messages/${messageId}/reaction`,
        {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                emoji
            })
        }
    );

    await loadMessages();
}


async function pinMessage(
    messageId
) {

    const data =
        await api(
            `/api/messages/${messageId}/pin`,
            {
                method: "POST"
            }
        );

    if (!data.success) {

        showToast(
            data.error ||
            "Nachricht konnte nicht angepinnt werden.",
            "error"
        );

        return;
    }

    await loadMessages();
}


/* =========================================================
   HUB TABS
========================================================= */

function showHubTab(
    tab
) {

    document
        .querySelectorAll(".hub-tab-content")
        .forEach(
            element =>
                element.classList.add(
                    "hidden"
                )
        );

    document
        .querySelectorAll(".hub-tab")
        .forEach(
            button =>
                button.classList.remove(
                    "active"
                )
        );

    const button =
        [...document.querySelectorAll(
            ".hub-tab"
        )].find(
            item =>
                item.textContent
                    .trim()
                    .toLowerCase()
                    === tab
        );

    if (button) {
        button.classList.add(
            "active"
        );
    }

    const target =
        {
            chat:
                "hubChat",

            overview:
                "hubOverviewTab",

            people:
                "hubPeopleTab",

            events:
                "hubEventsTab",

            tasks:
                "hubTasksTab",

            files:
                "hubFilesTab",

            notes:
                "hubNotesTab",

            activity:
                "hubActivityTab"

        }[tab];

    if (target) {

        $(target)
            .classList.remove(
                "hidden"
            );

    }

    if (tab === "overview") {
        renderHubOverview();
    }

    if (tab === "people") {
        renderHubPeople();
    }

    if (tab === "events") {
        loadEvents();
    }

    if (tab === "tasks") {
        loadTasks();
    }

    if (tab === "files") {
        loadFiles();
    }

    if (tab === "notes") {
        loadNotes();
    }

    if (tab === "activity") {
        loadActivity();
    }
}


/* =========================================================
   OVERVIEW
========================================================= */

async function renderHubOverview() {

    const container =
        $("hubOverviewTab");

    container.innerHTML =
        `
        <div class="data-grid">

            <div class="data-card">

                <h3>
                    ${currentHub.members.length}
                </h3>

                <p>
                    Members
                </p>

            </div>

            <div class="data-card">

                <h3>
                    ${currentHub.channels.length}
                </h3>

                <p>
                    Channels
                </p>

            </div>

            <div class="data-card">

                <h3>
                    ${
                        currentHub.public
                            ? "Public"
                            : "Private"
                    }
                </h3>

                <p>
                    Hub visibility
                </p>

            </div>

        </div>

        <div class="content-card" style="margin-top:15px">

            <h3>
                About this Hub
            </h3>

            <p>
                ${escapeHtml(
                    currentHub.description ||
                    "No description."
                )}
            </p>

            <h3>
                Rules
            </h3>

            <p>
                ${escapeHtml(
                    currentHub.rules ||
                    "No rules have been added."
                )}
            </p>

        </div>
        `;
}


/* =========================================================
   PEOPLE
========================================================= */

function renderHubPeople() {

    const container =
        $("hubPeopleTab");

    const role =
        getCurrentHubRole();

    const canInvite =
        ["owner", "admin"].includes(role);

    const canManageRoles =
        role === "owner";

    container.innerHTML =
        `
        ${
            canInvite
            ? `
            <div class="inline-form">

                <input
                    id="hubInviteUsername"
                    placeholder="Username to invite..."
                >

                <button
                    class="primary-button"
                    onclick="inviteUser()"
                >
                    Invite
                </button>

            </div>
            `
            : ""
        }

        <div class="subsection-heading">
            <div>
                <span class="eyebrow">MEMBERS</span>
                <h3>People in this Hub</h3>
            </div>
        </div>

        <div class="people-grid">

            ${
                currentHub.members
                    .map(
                        member => {

                            const isOwner =
                                member.role === "owner";

                            const canEdit =
                                canManageRoles &&
                                !isOwner;

                            return `
                            <div class="person-card">

                                <div class="avatar">
                                    ${escapeHtml(
                                        member.username
                                            .charAt(0)
                                            .toUpperCase()
                                    )}
                                </div>

                                <div class="person-info">

                                    <strong>
                                        ${escapeHtml(
                                            member.username
                                        )}
                                    </strong>

                                    <p>
                                        ${member.role === "owner"
                                            ? "Owner"
                                            : member.role === "admin"
                                                ? "Admin"
                                                : "Member"}
                                    </p>

                                </div>

                                ${
                                    canEdit
                                    ? `
                                    <div class="member-actions">

                                        <select
                                            class="member-role-select"
                                            onchange="changeMemberRole(
                                                ${member.user_id},
                                                this.value
                                            )"
                                        >
                                            <option
                                                value="member"
                                                ${member.role === "member" ? "selected" : ""}
                                            >
                                                Member
                                            </option>

                                            <option
                                                value="admin"
                                                ${member.role === "admin" ? "selected" : ""}
                                            >
                                                Admin
                                            </option>
                                        </select>

                                        <button
                                            class="ghost-button"
                                            onclick="removeHubMember(${member.user_id})"
                                        >
                                            Remove
                                        </button>

                                    </div>
                                    `
                                    : ""
                                }

                            </div>
                            `;
                        }
                    )
                    .join("")
            }

        </div>

        <div class="subsection-heading request-heading">
            <div>
                <span class="eyebrow">INVITE</span>
                <h3>Pending HUB invitations</h3>
            </div>
        </div>

        <div id="hubPendingInvitations" class="request-list">
            Loading...
        </div>
        `;

    loadHubInvitations();
}


async function loadHubInvitations() {

    const container =
        $("hubPendingInvitations");

    if (!container) {
        return;
    }

    const data =
        await api(
            "/api/invitations"
        );

    const invitations =
        data.invitations || [];

    if (!invitations.length) {
        container.innerHTML =
            `<div class="empty-state">No pending Hub invitations.</div>`;
        return;
    }

    container.innerHTML =
        invitations
            .map(
                invitation =>
                    `
                    <div class="request-card">

                        <div class="avatar">
                            ${escapeHtml(
                                invitation.sender_username
                                    .charAt(0)
                                    .toUpperCase()
                            )}
                        </div>

                        <div class="request-info">
                            <strong>
                                ${escapeHtml(
                                    invitation.sender_username
                                )}
                            </strong>
                            <p>
                                invited you to
                                <strong>
                                    ${escapeHtml(
                                        invitation.hub_name
                                    )}
                                </strong>
                            </p>
                        </div>

                        <div class="request-actions">
                            <button
                                class="primary-button"
                                onclick="handleHubInvitation(
                                    ${invitation.id},
                                    'accept'
                                )"
                            >
                                Accept
                            </button>

                            <button
                                class="ghost-button"
                                onclick="handleHubInvitation(
                                    ${invitation.id},
                                    'decline'
                                )"
                            >
                                Decline
                            </button>
                        </div>

                    </div>
                    `
            )
            .join("");
}


async function handleHubInvitation(
    invitationId,
    action
) {

    const data =
        await api(
            `/api/invitations/${invitationId}/${action}`,
            {
                method: "POST"
            }
        );

    if (!data.success) {
        showToast(
            data.error ||
            "Die Einladung konnte nicht verarbeitet werden.",
            "error"
        );
        return;
    }

    showToast(
        action === "accept"
            ? "Du bist dem HUB beigetreten."
            : "Einladung abgelehnt.",
        "success"
    );

    await loadHubs();
    await loadNotifications();

    if (currentHub) {
        renderHubPeople();
    }
}


async function changeMemberRole(
    userId,
    role
) {

    const data =
        await api(
            `/api/hubs/${currentHub.id}/members/${userId}/role`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    role
                })
            }
        );

    if (!data.success) {
        showToast(
            data.error ||
            "Rolle konnte nicht geändert werden.",
            "error"
        );
        return;
    }

    const refreshed =
        await api(
            `/api/hubs/${currentHub.id}`
        );

    currentHub =
        refreshed.hub;

    currentHub.members =
        refreshed.members;

    currentHub.channels =
        refreshed.channels;

    renderHubPeople();
    renderChannels();

    showToast(
        role === "admin"
            ? "Mitglied ist jetzt Admin."
            : "Admin wurde zurückgestuft.",
        "success"
    );
}



async function inviteUser() {

    const username =
        $("hubInviteUsername")
            .value
            .trim();

    if (!username) {
        return;
    }

    const data =
        await api(
            `/api/hubs/${currentHub.id}/invite`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    username
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error ||
            "Einladung fehlgeschlagen.",
            "error"
        );

        return;
    }

    $("hubInviteUsername")
        .value = "";

    showToast(
        "Einladung gesendet.",
        "success"
    );
}


async function removeHubMember(
    userId
) {

    openConfirm(
        "Mitglied entfernen",
        "Diese Person wird aus dem Hub entfernt.",
        async function () {

            const data =
                await api(
                    `/api/hubs/${currentHub.id}/members/${userId}`,
                    {
                        method: "DELETE"
                    }
                );

            if (!data.success) {

                showToast(
                    data.error ||
                    "Mitglied konnte nicht entfernt werden.",
                    "error"
                );

                return;
            }

            const refreshed =
                await api(
                    `/api/hubs/${currentHub.id}`
                );

            currentHub =
                refreshed.hub;

            currentHub.members =
                refreshed.members;

            currentHub.channels =
                refreshed.channels;

            renderHubPeople();

        }
    );
}


/* =========================================================
   EVENTS
========================================================= */

async function loadEvents() {

    const data =
        await api(
            `/api/hubs/${currentHub.id}/events`
        );

    const container =
        $("hubEventsTab");

    container.innerHTML =
        `
        <div class="inline-form">

            <input
                id="eventTitle"
                placeholder="Event title"
            >

            <input
                id="eventDate"
                type="datetime-local"
            >

            <button
                class="primary-button"
                onclick="createEvent()"
            >
                Add
            </button>

        </div>

        <div class="data-grid">

            ${
                (data.events || [])
                    .map(
                        event =>
                            `
                            <div class="data-card">

                                <h3>
                                    ${escapeHtml(
                                        event.title
                                    )}
                                </h3>

                                <p>
                                    ${escapeHtml(
                                        event.description ||
                                        "No description."
                                    )}
                                </p>

                                <small>
                                    ${escapeHtml(
                                        event.event_date
                                    )}
                                </small>

                            </div>
                            `
                    )
                    .join("")
            }

        </div>
        `;
}


async function createEvent() {

    const title =
        $("eventTitle")
            .value
            .trim();

    const eventDate =
        $("eventDate")
            .value;

    if (!title || !eventDate) {
        return;
    }

    const data =
        await api(
            `/api/hubs/${currentHub.id}/events`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    title,
                    event_date:
                        eventDate
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error,
            "error"
        );

        return;
    }

    loadEvents();
}


/* =========================================================
   TASKS
========================================================= */

async function loadTasks() {

    const data =
        await api(
            `/api/hubs/${currentHub.id}/tasks`
        );

    const container =
        $("hubTasksTab");

    container.innerHTML =
        `
        <div class="inline-form">

            <input
                id="taskTitle"
                placeholder="New task..."
            >

            <button
                class="primary-button"
                onclick="createTask()"
            >
                Add
            </button>

        </div>

        <div class="data-grid">

            ${
                (data.tasks || [])
                    .map(
                        task =>
                            `
                            <div class="data-card">

                                <h3>
                                    ${escapeHtml(
                                        task.title
                                    )}
                                </h3>

                                <p>
                                    ${escapeHtml(
                                        task.description ||
                                        ""
                                    )}
                                </p>

                                <select
                                    onchange="
                                        updateTaskStatus(
                                            ${task.id},
                                            this.value
                                        )
                                    "
                                >

                                    <option
                                        value="todo"
                                        ${
                                            task.status === "todo"
                                                ? "selected"
                                                : ""
                                        }
                                    >
                                        To do
                                    </option>

                                    <option
                                        value="doing"
                                        ${
                                            task.status === "doing"
                                                ? "selected"
                                                : ""
                                        }
                                    >
                                        In progress
                                    </option>

                                    <option
                                        value="done"
                                        ${
                                            task.status === "done"
                                                ? "selected"
                                                : ""
                                        }
                                    >
                                        Done
                                    </option>

                                </select>

                            </div>
                            `
                    )
                    .join("")
            }

        </div>
        `;
}


async function createTask() {

    const title =
        $("taskTitle")
            .value
            .trim();

    if (!title) {
        return;
    }

    const data =
        await api(
            `/api/hubs/${currentHub.id}/tasks`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    title
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error,
            "error"
        );

        return;
    }

    loadTasks();
}


async function updateTaskStatus(
    taskId,
    status
) {

    await api(
        `/api/tasks/${taskId}`,
        {
            method: "PUT",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                status
            })
        }
    );
}


/* =========================================================
   FILES
========================================================= */

async function loadFiles() {

    const data =
        await api(
            `/api/hubs/${currentHub.id}/files`
        );

    const container =
        $("hubFilesTab");

    container.innerHTML =
        `
        <div class="content-card">

            <input
                id="hubFileInput"
                type="file"
            >

            <button
                class="primary-button"
                style="margin-top:10px"
                onclick="uploadHubFile()"
            >
                Upload file
            </button>

        </div>

        <div
            class="data-grid"
            style="margin-top:15px"
        >

            ${
                (data.files || [])
                    .map(
                        file =>
                            `
                            <div class="data-card">

                                <h3>
                                    ${escapeHtml(
                                        file.filename
                                    )}
                                </h3>

                                <p>
                                    Uploaded by
                                    ${escapeHtml(
                                        file.username
                                    )}
                                </p>

                                <a
                                    href="${escapeHtml(file.url)}"
                                    target="_blank"
                                    class="secondary-button"
                                >
                                    Open
                                </a>

                            </div>
                            `
                    )
                    .join("")
            }

        </div>
        `;
}


async function uploadHubFile() {

    const file =
        $("hubFileInput")
            .files[0];

    if (!file) {
        return;
    }

    const form =
        new FormData();

    form.append(
        "file",
        file
    );

    const data =
        await api(
            `/api/hubs/${currentHub.id}/files`,
            {
                method: "POST",
                body: form
            }
        );

    if (!data.success) {

        showToast(
            data.error,
            "error"
        );

        return;
    }

    showToast(
        "Datei hochgeladen.",
        "success"
    );

    loadFiles();
}


/* =========================================================
   NOTES
========================================================= */

async function loadNotes() {

    const data =
        await api(
            `/api/hubs/${currentHub.id}/notes`
        );

    const container =
        $("hubNotesTab");

    container.innerHTML =
        `
        <div class="content-card">

            <input
                id="noteTitle"
                placeholder="Note title"
            >

            <textarea
                id="noteContent"
                placeholder="Write a shared note..."
            ></textarea>

            <button
                class="primary-button"
                onclick="createNote()"
            >
                Save note
            </button>

        </div>

        <div
            class="data-grid"
            style="margin-top:15px"
        >

            ${
                (data.notes || [])
                    .map(
                        note =>
                            `
                            <div class="data-card">

                                <h3>
                                    ${escapeHtml(
                                        note.title
                                    )}
                                </h3>

                                <p>
                                    ${escapeHtml(
                                        note.content
                                    )}
                                </p>

                                <small>
                                    ${escapeHtml(
                                        note.username
                                    )}
                                </small>

                            </div>
                            `
                    )
                    .join("")
            }

        </div>
        `;
}


async function createNote() {

    const title =
        $("noteTitle")
            .value
            .trim();

    const content =
        $("noteContent")
            .value
            .trim();

    if (!title) {
        return;
    }

    const data =
        await api(
            `/api/hubs/${currentHub.id}/notes`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    title,
                    content
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error,
            "error"
        );

        return;
    }

    loadNotes();
}


/* =========================================================
   ACTIVITY
========================================================= */

async function loadActivity() {

    const data =
        await api(
            `/api/hubs/${currentHub.id}/activity`
        );

    const container =
        $("hubActivityTab");

    container.innerHTML =
        `
        <div class="activity-list">

            ${
                (data.activity || [])
                    .map(
                        item =>
                            `
                            <div class="activity-item">

                                <div class="avatar">
                                    ${
                                        item.username
                                            ? item.username
                                                .charAt(0)
                                                .toUpperCase()
                                            : "H"
                                    }
                                </div>

                                <div>

                                    <p>
                                        <strong>
                                            ${escapeHtml(
                                                item.username ||
                                                "System"
                                            )}
                                        </strong>

                                        ${escapeHtml(
                                            item.action
                                        )}
                                    </p>

                                    <small>
                                        ${escapeHtml(
                                            item.details
                                        )}
                                        ·
                                        ${escapeHtml(
                                            item.created_at
                                        )}
                                    </small>

                                </div>

                            </div>
                            `
                    )
                    .join("")
            }

        </div>
        `;
}


/* =========================================================
   CHANNELS
========================================================= */

function openCreateChannel() {

    if (
        !currentHub ||
        !["owner", "admin"].includes(
            getCurrentHubRole()
        )
    ) {
        showToast(
            "Nur Owner und Admins können Kanäle erstellen.",
            "error"
        );
        return;
    }

    $("channelName").value = "";
    $("channelType").value = "text";
    $("channelCreateError").textContent = "";

    $("createChannelModal")
        .classList.remove("hidden");

    $("channelName").focus();
}


async function createChannel() {

    const name =
        $("channelName")
            .value
            .trim();

    const type =
        $("channelType")
            .value;

    if (!name) {
        $("channelCreateError")
            .textContent =
                "Bitte gib einen Kanalnamen ein.";
        return;
    }

    const data =
        await api(
            `/api/hubs/${currentHub.id}/channels`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    name,
                    type
                })
            }
        );

    if (!data.success) {

        $("channelCreateError")
            .textContent =
                data.error ||
                "Kanal konnte nicht erstellt werden.";

        return;
    }

    closeModal("createChannelModal");

    const refreshed =
        await api(
            `/api/hubs/${currentHub.id}`
        );

    currentHub =
        refreshed.hub;

    currentHub.members =
        refreshed.members;

    currentHub.channels =
        refreshed.channels;

    renderChannels();

    showToast(
        "Kanal erstellt.",
        "success"
    );
}


/* =========================================================
   DISCOVER
========================================================= */

async function openDiscover() {

    hideAllPages();

    $("discoverPage")
        .classList.remove(
            "hidden"
        );

    $("topbarTitle")
        .textContent =
            "Discover";

    const data =
        await api(
            "/api/discover"
        );

    $("discoverGrid")
        .innerHTML =
            (data.hubs || [])
                .map(
                    hub =>
                        `
                        <div class="discover-card">

                            <div
                                class="hub-large-icon"
                                style="
                                    width:46px;
                                    height:46px;
                                    background:${hub.color}22;
                                    color:${hub.color};
                                    margin-bottom:12px;
                                "
                            >
                                ${
                                    hub.icon_type === "image"
                                    ? `
                                    <img
                                        src="${escapeHtml(hub.icon)}"
                                        alt=""
                                    >
                                    `
                                    : escapeHtml(
                                        hub.icon
                                    )
                                }
                            </div>

                            <h3>
                                ${escapeHtml(
                                    hub.name
                                )}
                            </h3>

                            <p>
                                ${escapeHtml(
                                    hub.description ||
                                    "Public Hub"
                                )}
                            </p>

                            <small>
                                ${hub.member_count}
                                members
                            </small>

                        </div>
                        `
                )
                .join("");
}


/* =========================================================
   PEOPLE PAGE
========================================================= */

async function openFriends() {

    hideAllPages();

    $("peoplePage")
        .classList.remove(
            "hidden"
        );

    $("topbarTitle")
        .textContent =
            "People";

    await loadFriends();
}


async function searchPeoplePage() {

    const query =
        $("peopleSearch")
            .value
            .trim();

    if (query.length < 1) {

        $("peopleResults")
            .innerHTML = "";

        return;
    }

    const data =
        await api(
            `/api/users/search?q=${encodeURIComponent(query)}`
        );

    $("peopleResults")
        .innerHTML =
            (data.users || [])
                .map(
                    user =>
                        `
                        <div class="person-card">

                            <div class="avatar">
                                ${escapeHtml(
                                    user.username
                                        .charAt(0)
                                        .toUpperCase()
                                )}
                            </div>

                            <div class="person-info">

                                <strong>
                                    ${escapeHtml(
                                        user.username
                                    )}
                                </strong>

                                <p>
                                    ${escapeHtml(
                                        user.bio ||
                                        "HUB user"
                                    )}
                                </p>

                            </div>

                            <button
                                class="secondary-button"
                                onclick="sendFriendRequest(${user.id})"
                            >
                                Add
                            </button>

                        </div>
                        `
                )
                .join("");
}


async function sendFriendRequest(
    userId
) {

    const data =
        await api(
            "/api/friends/request",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    user_id:
                        userId
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error,
            "error"
        );

        return;
    }

    showToast(
        "Freundschaftsanfrage gesendet.",
        "success"
    );

    await loadFriends();
}


async function loadFriends() {

    const data =
        await api(
            "/api/friends"
        );

    const friends =
        data.friends || [];

    const incoming =
        friends.filter(
            friend =>
                friend.status === "pending" &&
                friend.receiver_id === currentUser.id
        );

    const outgoing =
        friends.filter(
            friend =>
                friend.status === "pending" &&
                friend.sender_id === currentUser.id
        );

    const accepted =
        friends.filter(
            friend =>
                friend.status === "accepted"
        );

    const requestContainer =
        $("friendRequestsList");

    if (requestContainer) {

        requestContainer.innerHTML =
            incoming.length
            ? incoming
                .map(
                    friend =>
                        `
                        <div class="request-card">

                            <div class="avatar">
                                ${escapeHtml(
                                    friend.username
                                        .charAt(0)
                                        .toUpperCase()
                                )}
                            </div>

                            <div class="request-info">
                                <strong>
                                    ${escapeHtml(
                                        friend.username
                                    )}
                                </strong>
                                <p>
                                    möchte mit dir befreundet sein.
                                </p>
                            </div>

                            <div class="request-actions">

                                <button
                                    class="primary-button"
                                    onclick="handleFriendRequest(
                                        ${friend.id},
                                        'accept'
                                    )"
                                >
                                    Accept
                                </button>

                                <button
                                    class="ghost-button"
                                    onclick="handleFriendRequest(
                                        ${friend.id},
                                        'decline'
                                    )"
                                >
                                    Decline
                                </button>

                            </div>

                        </div>
                        `
                )
                .join("")
            : `<div class="empty-state">Keine offenen Freundschaftsanfragen.</div>`;

    }

    const outgoingContainer =
        $("outgoingFriendRequests");

    if (outgoingContainer) {

        outgoingContainer.innerHTML =
            outgoing.length
            ? outgoing
                .map(
                    friend =>
                        `
                        <div class="request-card compact-request">

                            <div class="avatar">
                                ${escapeHtml(
                                    friend.username
                                        .charAt(0)
                                        .toUpperCase()
                                )}
                            </div>

                            <div class="request-info">
                                <strong>
                                    ${escapeHtml(
                                        friend.username
                                    )}
                                </strong>
                                <p>Ausstehende Anfrage</p>
                            </div>

                        </div>
                        `
                )
                .join("")
            : `<div class="empty-state">Keine ausgehenden Anfragen.</div>`;
    }

    $("friendsList")
        .innerHTML =
            accepted
                .map(
                    friend =>
                        `
                        <div class="person-card">

                            <div class="avatar">
                                ${escapeHtml(
                                    friend.username
                                        .charAt(0)
                                        .toUpperCase()
                                )}
                            </div>

                            <div class="person-info">

                                <strong>
                                    ${escapeHtml(
                                        friend.username
                                    )}
                                </strong>

                                <p>
                                    ${escapeHtml(
                                        friend.bio ||
                                        "HUB user"
                                    )}
                                </p>

                            </div>

                        </div>
                        `
                )
                .join("");

    await loadHubInvitationsForPeople();
}


async function handleFriendRequest(
    requestId,
    action
) {

    const data =
        await api(
            `/api/friends/${requestId}/${action}`,
            {
                method: "POST"
            }
        );

    if (!data.success) {
        showToast(
            data.error ||
            "Anfrage konnte nicht verarbeitet werden.",
            "error"
        );
        return;
    }

    showToast(
        action === "accept"
            ? "Freundschaftsanfrage angenommen."
            : "Freundschaftsanfrage abgelehnt.",
        "success"
    );

    await loadFriends();
    await loadNotifications();
}


async function loadHubInvitationsForPeople() {

    const container =
        $("peopleHubInvitations");

    if (!container) {
        return;
    }

    const data =
        await api(
            "/api/invitations"
        );

    const invitations =
        data.invitations || [];

    container.innerHTML =
        invitations.length
        ? invitations
            .map(
                invitation =>
                    `
                    <div class="request-card">

                        <div class="avatar">
                            ${escapeHtml(
                                invitation.sender_username
                                    .charAt(0)
                                    .toUpperCase()
                            )}
                        </div>

                        <div class="request-info">
                            <strong>
                                ${escapeHtml(
                                    invitation.sender_username
                                )}
                            </strong>
                            <p>
                                hat dich in
                                <strong>
                                    ${escapeHtml(
                                        invitation.hub_name
                                    )}
                                </strong>
                                eingeladen.
                            </p>
                        </div>

                        <div class="request-actions">

                            <button
                                class="primary-button"
                                onclick="handleHubInvitation(
                                    ${invitation.id},
                                    'accept'
                                )"
                            >
                                Join
                            </button>

                            <button
                                class="ghost-button"
                                onclick="handleHubInvitation(
                                    ${invitation.id},
                                    'decline'
                                )"
                            >
                                Decline
                            </button>

                        </div>

                    </div>
                    `
            )
            .join("")
        : `<div class="empty-state">Keine offenen HUB-Einladungen.</div>`;
}



/* =========================================================
   GLOBAL SEARCH
========================================================= */

function openSearch() {

    $("searchModal")
        .classList.remove(
            "hidden"
        );

    $("globalSearchInput")
        .focus();
}


async function globalSearch() {

    const query =
        $("globalSearchInput")
            .value
            .trim();

    const container =
        $("globalSearchResults");

    if (query.length < 2) {

        container.innerHTML = "";

        return;
    }

    const data =
        await api(
            `/api/search?q=${encodeURIComponent(query)}`
        );

    let html = "";


    if (
        data.users &&
        data.users.length
    ) {

        html +=
            `
            <div class="eyebrow">
                PEOPLE
            </div>
            `;

        data.users.forEach(
            user => {

                html +=
                    `
                    <div class="search-result">

                        <strong>
                            ${escapeHtml(
                                user.username
                            )}
                        </strong>

                        <small>
                            ${escapeHtml(
                                user.bio || "HUB user"
                            )}
                        </small>

                    </div>
                    `;

            }
        );

    }


    if (
        data.hubs &&
        data.hubs.length
    ) {

        html +=
            `
            <div class="eyebrow" style="margin-top:18px">
                HUBS
            </div>
            `;

        data.hubs.forEach(
            hub => {

                html +=
                    `
                    <div
                        class="search-result"
                        onclick="${
                            hub.public
                            ? `closeModal('searchModal'); openHub(${hub.id})`
                            : ""
                        }"
                    >

                        <strong>
                            ${escapeHtml(
                                hub.name
                            )}
                        </strong>

                        <small>
                            ${escapeHtml(
                                hub.description || ""
                            )}
                        </small>

                    </div>
                    `;

            }
        );

    }


    if (
        data.messages &&
        data.messages.length
    ) {

        html +=
            `
            <div class="eyebrow" style="margin-top:18px">
                MESSAGES
            </div>
            `;

        data.messages.forEach(
            message => {

                html +=
                    `
                    <div class="search-result">

                        <strong>
                            ${escapeHtml(
                                message.username
                            )}
                        </strong>

                        <small>
                            ${escapeHtml(
                                message.content
                            )}
                        </small>

                        <small>
                            ${escapeHtml(
                                message.hub_name
                            )}
                            /
                            #${escapeHtml(
                                message.channel_name
                            )}
                        </small>

                    </div>
                    `;

            }
        );

    }


    if (!html) {

        html =
            `
            <div class="data-card">
                <p>No results.</p>
            </div>
            `;

    }

    container.innerHTML =
        html;
}


/* =========================================================
   INVITE LINK
========================================================= */

async function createInviteLink() {

    const data =
        await api(
            `/api/hubs/${currentHub.id}/invite-link`,
            {
                method: "POST"
            }
        );

    if (!data.success) {

        showToast(
            data.error ||
            "Link konnte nicht erstellt werden.",
            "error"
        );

        return;
    }

    showToast(
        "Invite-Code: " + data.code,
        "success"
    );
}


/* =========================================================
   NOTIFICATIONS
========================================================= */

async function loadNotifications() {

    const data =
        await api(
            "/api/notifications"
        );

    const badge =
        $("notificationBadge");

    if (
        data.unread > 0
    ) {

        badge.textContent =
            data.unread;

        badge.classList.remove(
            "hidden"
        );

    } else {

        badge.classList.add(
            "hidden"
        );

    }
}


async function openNotifications() {

    $("notificationsModal")
        .classList.remove(
            "hidden"
        );

    const data =
        await api(
            "/api/notifications"
        );

    $("notificationList")
        .innerHTML =
            (data.notifications || [])
                .map(
                    notification =>
                        `
                        <div
                            class="notification-item ${
                                notification.read
                                    ? ""
                                    : "unread"
                            }"
                        >

                            <strong>
                                ${escapeHtml(
                                    notification.title
                                )}
                            </strong>

                            <p>
                                ${escapeHtml(
                                    notification.content
                                )}
                            </p>

                            <small>
                                ${escapeHtml(
                                    notification.created_at
                                )}
                            </small>

                        </div>
                        `
                )
                .join("");

    await api(
        "/api/notifications/read",
        {
            method: "POST"
        }
    );

    await loadNotifications();
}


/* =========================================================
   SETTINGS
========================================================= */

function openSettings() {

    updateUserUI();

    $("settingsModal")
        .classList.remove(
            "hidden"
        );
}


async function saveProfileSettings() {

    const username =
        $("settingsUsername")
            .value
            .trim();

    const bio =
        $("settingsBio")
            .value
            .trim();

    $("profileSettingsError")
        .textContent = "";

    const usernameData =
        await api(
            "/api/settings/username",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    username
                })
            }
        );

    if (
        !usernameData.success
    ) {

        $("profileSettingsError")
            .textContent =
                usernameData.error;

        return;
    }

    const settingsData =
        await api(
            "/api/settings",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    bio
                })
            }
        );

    if (
        !settingsData.success
    ) {

        $("profileSettingsError")
            .textContent =
                settingsData.error;

        return;
    }

    const me =
        await api(
            "/api/me"
        );

    currentUser =
        me.user;

    updateUserUI();

    showToast(
        "Profil gespeichert.",
        "success"
    );
}


async function saveGeneralSettings() {

    const data =
        await api(
            "/api/settings",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    theme:
                        $("settingsTheme")
                            .value,

                    compact_mode:
                        $("settingsCompact")
                            .checked,

                    notifications:
                        $("settingsNotifications")
                            .checked,

                    bio:
                        $("settingsBio")
                            .value
                            .trim()
                })
            }
        );

    if (!data.success) {

        showToast(
            data.error,
            "error"
        );

        return;
    }

    currentUser.theme =
        $("settingsTheme")
            .value;

    currentUser.compact_mode =
        $("settingsCompact")
            .checked;

    currentUser.notifications =
        $("settingsNotifications")
            .checked;

    applyUserSettings();

    showToast(
        "Einstellungen gespeichert.",
        "success"
    );
}


async function changePassword() {

    $("passwordError")
        .textContent = "";

    const data =
        await api(
            "/api/settings/password",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({

                    old_password:
                        $("oldPassword")
                            .value,

                    new_password:
                        $("newPassword")
                            .value

                })
            }
        );

    if (!data.success) {

        $("passwordError")
            .textContent =
                data.error;

        return;
    }

    $("oldPassword")
        .value = "";

    $("newPassword")
        .value = "";

    showToast(
        "Passwort geändert.",
        "success"
    );
}


/* =========================================================
   PROFILE
========================================================= */

function openProfile() {

    updateUserUI();

    $("profileModal")
        .classList.remove(
            "hidden"
        );
}


/* =========================================================
   CONFIRMATION
========================================================= */

function openConfirm(
    title,
    text,
    action
) {

    $("confirmTitle")
        .textContent =
            title;

    $("confirmText")
        .textContent =
            text;

    $("confirmAction")
        .onclick =
            async function () {

                closeModal(
                    "confirmModal"
                );

                await action();

            };

    $("confirmModal")
        .classList.remove(
            "hidden"
        );
}


function confirmDeleteHub() {

    openConfirm(
        "Hub löschen",
        "Dieser Hub und seine Inhalte werden dauerhaft gelöscht.",
        async function () {

            const data =
                await api(
                    `/api/hubs/${currentHub.id}`,
                    {
                        method: "DELETE"
                    }
                );

            if (!data.success) {

                showToast(
                    data.error ||
                    "Hub konnte nicht gelöscht werden.",
                    "error"
                );

                return;
            }

            currentHub =
                null;

            currentChannel =
                null;

            await loadHubs();

            showHome();

            showToast(
                "Hub gelöscht.",
                "success"
            );

        }
    );
}


/* =========================================================
   MODALS
========================================================= */

function closeModal(
    id
) {

    $(id)
        .classList.add(
            "hidden"
        );
}


document
    .querySelectorAll(".modal")
    .forEach(
        modal => {

            modal.addEventListener(
                "click",
                event => {

                    if (
                        event.target === modal
                    ) {

                        modal.classList.add(
                            "hidden"
                        );

                    }

                }
            );

        }
    );


document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape"
        ) {

            document
                .querySelectorAll(".modal")
                .forEach(
                    modal =>
                        modal.classList.add(
                            "hidden"
                        )
                );

        }

        if (
            event.key === "/" &&
            document.activeElement.tagName !== "INPUT" &&
            document.activeElement.tagName !== "TEXTAREA"
        ) {

            event.preventDefault();

            openSearch();

        }

    }
);


/* =========================================================
   MOBILE
========================================================= */

function toggleSidebar() {

    document
        .querySelector(".sidebar")
        .classList.toggle(
            "mobile-open"
        );
}


/* =========================================================
   DATE
========================================================= */

function formatDate(
    value
) {

    if (!value) {
        return "";
    }

    const date =
        new Date(
            value.replace(
                " ",
                "T"
            )
        );

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;

    }

    return date.toLocaleString(
        "de-DE",
        {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        }
    );
}


/* =========================================================
   START
========================================================= */

checkLogin();
