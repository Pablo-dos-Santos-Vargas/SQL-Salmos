// ======================================================
//  CONFIGURAÇÃO DA CÂMERA
// ======================================================

let stream = null;
let currentFacing = "environment"; // environment | user

async function startCamera() {
    stopCamera();
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { ideal: currentFacing } },
            audio: false
        });

        document.getElementById("video").srcObject = stream;
        setStatus("Câmera iniciada.");

    } catch (err) {
        setError("Erro ao acessar a câmera: " + err.message);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    document.getElementById("video").srcObject = null;
    setStatus("Câmera parada.");
}

function switchCamera() {
    currentFacing = currentFacing === "environment" ? "user" : "environment";
    startCamera();
}


// ======================================================
//  CAPTURA DA IMAGEM + ENVIO PARA FLASK
// ======================================================

async function captureAndSend() {
    const video = document.getElementById("video");
    if (!video.srcObject) {
        setError("Inicie a câmera antes de capturar.");
        return;
    }

    const canvas = document.getElementById("canvas");
    const w = video.videoWidth;
    const h = video.videoHeight;

    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, w, h);

    // preview
    document.getElementById("shot").src = canvas.toDataURL("image/jpeg", 0.9);

    setStatus("Enviando imagem...");

    canvas.toBlob(async blob => {
        const form = new FormData();
        form.append("imagem", blob, "captura.jpg");

        try {
            const resp = await fetch("/api/upload", {
                method: "POST",
                body: form
            });

            if (!resp.ok) {
                throw new Error("HTTP " + resp.status);
            }

            const data = await resp.json();

            if (data.status === "erro")
                throw new Error(data.mensagem);

            renderResults(data.dados_lidos || {});
            setStatus("Análise concluída!");

        } catch (err) {
            setError("Falha: " + err.message);
            setStatus("Erro na análise.");
        }
    }, "image/jpeg", 0.9);
}


// ======================================================
//  RENDERIZAÇÃO DOS RESULTADOS NO HTML
// ======================================================

function renderResults(dados) {
    const tbody = document.getElementById("results-body");
    tbody.innerHTML = "";

    // -----------------------
    // 1) CAMPOS PRINCIPAIS
    // -----------------------
    const camposCabecalho = [
        "Data",
        "Item",
        "QntPecas",
        "Maquina",
        "Setor",
        "NomeCracha"
    ];

    camposCabecalho.forEach(campo => {
        const valor = dados[campo] || "";
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${campo}</td>
            <td>${valor}</td>
            <td></td>
        `;
        tbody.appendChild(tr);
    });

    // -----------------------
    // 2) CAMPOS BOOLEANOS
    // (marcados pela IA)
    // -----------------------
    const camposBooleanos = [
        "Montagem",
        "Regulagem",
        "MarcaRetifica",
        "Empenamento",
        "FalhaRaio",
        "FalhaZinco",
        "Rebarba",
        "Batida",
        "Risco",
        "Trepidacao",
        "Ressalto",
        "Oxidacao",
        "DiametroInt",
        "DiametroExt",
        "Comprimento",
        "DimensaoMaior",
        "Menor",
        "Outros"
    ];

    camposBooleanos.forEach(campo => {
        const valor = dados[campo];
        if (valor === true) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${campo}</td>
                <td>Sim</td>
                <td>✔</td>
            `;
            tbody.appendChild(tr);
        }
    });

    // -----------------------
    // 3) CAMPOS TEXTO EXTRAS
    // -----------------------
    const camposExtras = [
        "DiametroIntDimensao",
        "DiametroExtDimensao",
        "ComprimentoDimensao",
        "OutrosDescricao",
        "Observacoes"
    ];

    camposExtras.forEach(campo => {
        const valor = dados[campo];
        if (valor && valor !== "") {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${campo}</td>
                <td>${valor}</td>
                <td></td>
            `;
            tbody.appendChild(tr);
        }
    });
}


// ======================================================
//  STATUS E ERROS NO HTML
// ======================================================

function setStatus(msg) {
    document.getElementById("status").textContent = msg;
}

function setError(msg) {
    document.getElementById("error").textContent = msg;
}


// ======================================================
//  EVENTOS
// ======================================================

document.getElementById("btn-start").onclick = startCamera;
document.getElementById("btn-stop").onclick = stopCamera;
document.getElementById("btn-switch").onclick = switchCamera;
document.getElementById("btn-capture").onclick = captureAndSend;

// Inicializa automaticamente, se permitido
if (
    navigator.mediaDevices &&
    (location.protocol.startsWith("https") || location.hostname === "localhost")
) {
    startCamera();
}
