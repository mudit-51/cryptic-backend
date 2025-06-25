const API_BASE = "http://localhost:8000";

function showMessage(msg, section) {
    // Map section argument to correct message div
    let map = {
        fileSection: 'message-files',
        accessSection: 'message-access',
        grantSection: 'message-grant',
        deleteSection: 'message-delete',
        files: 'message-files',
        access: 'message-access',
        grant: 'message-grant',
        delete: 'message-delete'
    };
    // Default to currently visible section if not provided
    if (!section) {
        if (document.getElementById('fileSection').style.display === 'block') section = 'fileSection';
        else if (document.getElementById('accessSection').style.display === 'block') section = 'accessSection';
        else if (document.getElementById('grantSection').style.display === 'block') section = 'grantSection';
        else if (document.getElementById('deleteSection').style.display === 'block') section = 'deleteSection';
    }
    // Clear all message boxes
    Object.values(map).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '';
    });
    // Set message in correct box
    if (map[section]) {
        document.getElementById(map[section]).textContent = msg;
    }
}

function loadFiles() {
    const clientId = 'pwnd'; // Hardcoded client ID
    fetch(`${API_BASE}/filelist?client_id=${clientId}`)
        .then(res => res.json())
        .then(data => {
            if (data.files) {
                const fileList = document.getElementById("fileList");
                fileList.innerHTML = "";
                data.files.forEach(f => {
                    const li = document.createElement("li");
                    let details = `<b>${f.file_name}</b>`;
                    if (f.size !== undefined && f.size !== null) {
                        details += ` <span style='color:#888;font-size:0.97em;'>(Size: ${f.size} bytes)</span>`;
                    }
                    if (f.last_modified_str) {
                        details += ` <span style='color:#888;font-size:0.97em;'>(Last Modified: ${f.last_modified_str})</span>`;
                    }
                    // Add delete button
                    details += ` <button class='delete-btn' onclick=\"deleteFileFromList('${f.file_name}')\">Delete</button>`;
                    li.innerHTML = details;
                    li.style.cursor = "pointer";
                    li.onclick = function(e) {
                        // Prevent click event if delete button is clicked
                        if (e.target && e.target.classList.contains('delete-btn')) return;
                        document.getElementById("accessFileName").value = f.file_name || '';
                        document.getElementById("grantFileName").value = f.file_name || '';
                        showMessage(`Selected file: ${f.file_name || ''}`, 'fileSection');
                    };
                    fileList.appendChild(li);
                });
                showMessage("", 'fileSection');
            } else {
                showMessage(data.error || "No files found.", 'fileSection');
            }
        })
        .catch(() => showMessage("Failed to load files.", 'fileSection'));
}

function deleteFileFromList(fileName) {
    const clientId = 'pwnd';
    if (!fileName || !clientId) {
        showMessage("File name and client ID are required to delete a file.", 'fileSection');
        return;
    }
    fetch(`${API_BASE}/deletefile?file_name=${encodeURIComponent(fileName)}&client_id=${clientId}`, {
        method: "DELETE"
    })
        .then(res => res.json())
        .then(data => {
            if (typeof data.message !== 'undefined') showMessage(data.message, 'fileSection');
            else if (typeof data.error !== 'undefined') showMessage(data.error, 'fileSection');
            else showMessage("Unexpected response: " + JSON.stringify(data), 'fileSection');
            loadFiles();
        })
        .catch(() => showMessage("Failed to delete file.", 'fileSection'));
}

function requestAccess() {
    const fileName = document.getElementById("accessFileName").value.trim();
    const clientId = document.getElementById("clientId").value.trim();
    const requesterId = document.getElementById("requesterId").value.trim();
    if (!fileName || !clientId || !requesterId) {
        showMessage("All fields are required for access request.", 'accessSection');
        return;
    }
    const url = `${API_BASE}/accessrequest?file_name=${encodeURIComponent(fileName)}&client_id=${encodeURIComponent(clientId)}&requester_id=${encodeURIComponent(requesterId)}`;
    fetch(url, {
        method: "POST"
    })
        .then(res => res.json())
        .then(data => {
            if (typeof data.message !== 'undefined') showMessage(data.message, 'accessSection');
            else if (typeof data.error !== 'undefined') showMessage(data.error, 'accessSection');
            else showMessage("Unexpected response: " + JSON.stringify(data), 'accessSection');
        })
        .catch(() => showMessage("Failed to request access.", 'accessSection'));
}

function grantAccess(grant) {
    const fileName = document.getElementById("grantFileName").value.trim();
    const ownerId = document.getElementById("ownerId").value.trim();
    const requesterId = document.getElementById("grantRequesterId").value.trim();
    if (!fileName || !ownerId || !requesterId) {
        showMessage("All fields are required to grant/deny access.", 'grantSection');
        return;
    }
    const url = `${API_BASE}/accesscontrol?file_name=${encodeURIComponent(fileName)}&owner_id=${encodeURIComponent(ownerId)}&requester_id=${encodeURIComponent(requesterId)}&grant=${grant}`;
    fetch(url, {
        method: "POST"
    })
        .then(res => res.json())
        .then(data => {
            if (typeof data.message !== 'undefined') showMessage(data.message, 'grantSection');
            else if (typeof data.error !== 'undefined') showMessage(data.error, 'grantSection');
            else showMessage("Unexpected response: " + JSON.stringify(data), 'grantSection');
        })
        .catch(() => showMessage("Failed to process access control.", 'grantSection'));
}

function loadRequests() {
    const ownerId = 'pwnd'; // Hardcoded owner ID
    fetch(`${API_BASE}/allrequests?client_id=${encodeURIComponent(ownerId)}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("requestsContainer");
            container.innerHTML = "";
            if (!data.requests || data.requests.length === 0) {
                container.innerHTML = '<div style="color:#888;">No requests found.</div>';
                return;
            }
            data.requests.forEach(req => {
                const card = document.createElement('div');
                card.className = 'request-card';
                let statusHtml = req.status ? '<span style=\'color:green\'>Active</span>' : '<span style=\'color:orange\'>Pending</span>';
                let btns = `
                    <div class=\"grant-btns\">
                        <button ${req.status ? 'disabled' : ''} onclick=\"handleGrantDeny('${req.file_name}','${req.client_id}','${req.recipient_id}',true)\">Grant</button>
                        <button ${req.status ? 'disabled' : ''} onclick=\"handleGrantDeny('${req.file_name}','${req.client_id}','${req.recipient_id}',false)\">Deny</button>
                        ${req.status ? `<button style='background:#e74c3c;margin-left:8px;' onclick=\"handleRevokeAccess('${req.file_name}','${req.client_id}','${req.recipient_id}')\">Revoke Access</button>` : ''}
                    </div>
                `;
                card.innerHTML = `
                    <div><b>File:</b> ${req.file_name}</div>
                    <div><b>Requester:</b> ${req.recipient_id}</div>
                    <div><b>Status:</b> ${statusHtml}</div>
                    ${btns}
                `;
                card.style.marginBottom = '18px';
                card.style.padding = '16px';
                card.style.background = '#f7f8fa';
                card.style.borderRadius = '8px';
                card.style.boxShadow = '0 1px 4px rgba(60,72,88,0.06)';
                container.appendChild(card);
            });
        })
        .catch(() => showMessage("Failed to load requests.", 'grantSection'));
}

function handleGrantDeny(fileName, ownerId, requesterId, grant) {
    ownerId = 'pwnd'; // Hardcoded owner ID
    fetch(`${API_BASE}/accesscontrol?file_name=${encodeURIComponent(fileName)}&owner_id=${encodeURIComponent(ownerId)}&requester_id=${encodeURIComponent(requesterId)}&grant=${grant}`, {
        method: "POST"
    })
        .then(res => res.json())
        .then(data => {
            showMessage(data.message || data.error || "Done", 'grantSection');
            loadRequests();
        })
        .catch(() => showMessage("Failed to process request.", 'grantSection'));
}

function handleRevokeAccess(fileName, ownerId, requesterId) {
    ownerId = 'pwnd'; // Hardcoded owner ID
    fetch(`${API_BASE}/revokeaccess?file_name=${encodeURIComponent(fileName)}&owner_id=${encodeURIComponent(ownerId)}&requester_id=${encodeURIComponent(requesterId)}`)
        .then(res => res.json())
        .then(data => {
            showMessage(data.message || data.error || "Done", 'grantSection');
            loadRequests();
        })
        .catch(() => showMessage("Failed to revoke access.", 'grantSection'));
}

// Load requests automatically when Grant/Deny section is shown
const origShowSection = window.showSection;
window.showSection = function(section) {
    origShowSection(section);
    if (section === 'grantSection') {
        loadRequests();
    }
};

window.addEventListener('DOMContentLoaded', function() {
    loadFiles();
});
