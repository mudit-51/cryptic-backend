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
    const clientId = document.getElementById("clientId").value.trim();
    if (!clientId) {
        showMessage("Please enter your client ID.", 'fileSection');
        return;
    }
    fetch(`${API_BASE}/filelist?client_id=${clientId}`)
        .then(res => res.json())
        .then(data => {
            if (data.files) {
                const fileList = document.getElementById("fileList");
                fileList.innerHTML = "";
                data.files.forEach(f => {
                    const li = document.createElement("li");
                    li.innerText = f.file_name;
                    li.style.cursor = "pointer";
                    li.onclick = function() {
                        document.getElementById("accessFileName").value = f.file_name || '';
                        document.getElementById("grantFileName").value = f.file_name || '';
                        document.getElementById("deleteFileName").value = f.file_name || '';
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

function deleteFile() {
    const fileName = document.getElementById("deleteFileName").value.trim();
    const clientId = document.getElementById("deleteClientId").value.trim();
    if (!fileName || !clientId) {
        showMessage("File name and client ID are required to delete a file.", 'deleteSection');
        return;
    }
    fetch(`${API_BASE}/deletefile?file_name=${fileName}&client_id=${clientId}`, {
        method: "DELETE"
    })
        .then(res => res.json())
        .then(data => {
            if (typeof data.message !== 'undefined') showMessage(data.message, 'deleteSection');
            else if (typeof data.error !== 'undefined') showMessage(data.error, 'deleteSection');
            else showMessage("Unexpected response: " + JSON.stringify(data), 'deleteSection');
        })
        .catch(() => showMessage("Failed to delete file.", 'deleteSection'));
}
