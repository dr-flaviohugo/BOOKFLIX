const apiRequest = window.BookflixApi.apiFetch;
const createSessionId = window.BookflixApi.getSessionId;

const state = {
  books: [],
  selectedBook: null,
  chapterManifest: null,
  currentChunk: 0,
  sessionId: createSessionId(),
};

const uploadInput = document.getElementById("epub-file");
const uploadBtn = document.getElementById("upload-btn");
const uploadStatus = document.getElementById("upload-status");
const bookList = document.getElementById("book-list");
const chapterSelect = document.getElementById("chapter-select");
const nowPlaying = document.getElementById("now-playing");
const speedSelect = document.getElementById("speed-select");
const voiceInput = document.getElementById("voice-input");
const voiceSave = document.getElementById("voice-save");
const playBtn = document.getElementById("play-btn");
const pauseBtn = document.getElementById("pause-btn");
const bookmarkBtn = document.getElementById("bookmark-btn");
const playerStatus = document.getElementById("player-status");
const audio = document.getElementById("audio-player");
const bookmarkList = document.getElementById("bookmark-list");

function setStatus(target, text) {
  target.textContent = text;
}

async function loadBooks() {
  try {
    state.books = await apiRequest("/api/v1/books");
    renderBooks();
  } catch (err) {
    setStatus(uploadStatus, `Erro ao carregar livros: ${err.message}`);
  }
}

function renderBooks() {
  bookList.innerHTML = "";
  if (!state.books.length) {
    const item = document.createElement("li");
    item.textContent = "Nenhum livro ainda";
    bookList.appendChild(item);
    return;
  }

  state.books.forEach((book) => {
    const item = document.createElement("li");
    item.className = "book-item";
    item.innerHTML = `<strong>${book.title}</strong><br><small>${book.author || "Autor desconhecido"}</small>`;

    const btn = document.createElement("button");
    btn.textContent = "Abrir";
    btn.addEventListener("click", () => openBook(book.id));
    item.appendChild(btn);

    bookList.appendChild(item);
  });
}

async function openBook(bookId) {
  state.selectedBook = await apiRequest(`/api/v1/books/${bookId}`);
  nowPlaying.textContent = `${state.selectedBook.title} - pronto para tocar`;

  chapterSelect.innerHTML = "";
  state.selectedBook.chapters.forEach((chapter) => {
    const option = document.createElement("option");
    option.value = String(chapter.chapter_index);
    option.textContent = `${chapter.chapter_index + 1}. ${chapter.title}`;
    chapterSelect.appendChild(option);
  });

  await loadProgress();
  await loadChapterManifest();
  await loadBookmarks();
}

async function loadChapterManifest() {
  if (!state.selectedBook) {
    return;
  }

  const chapterIndex = Number(chapterSelect.value || 0);
  state.chapterManifest = await apiRequest(
    `/api/v1/audio/${state.selectedBook.id}/chapter/${chapterIndex}/manifest`
  );
  state.currentChunk = 0;
  setStatus(playerStatus, `Capítulo ${chapterIndex + 1} carregado com ${state.chapterManifest.total_chunks} chunks`);
}

async function playCurrentChunk() {
  if (!state.selectedBook || !state.chapterManifest) {
    setStatus(playerStatus, "Selecione um livro primeiro");
    return;
  }

  const chapterIndex = Number(chapterSelect.value || 0);
  const chunk = state.chapterManifest.chunks[state.currentChunk];
  if (!chunk) {
    setStatus(playerStatus, "Fim do capítulo");
    await saveProgress(chapterIndex, audio.currentTime || 0);
    return;
  }

  const src = `${window.BookflixApi.API_BASE}${chunk.stream_url}`;
  audio.src = src;
  audio.playbackRate = Number(speedSelect.value);
  await audio.play();
  setStatus(playerStatus, `Reproduzindo chunk ${state.currentChunk + 1}/${state.chapterManifest.total_chunks}`);
}

async function saveProgress(chapterIndex, positionSeconds) {
  if (!state.selectedBook) {
    return;
  }

  try {
    await apiRequest("/api/v1/progress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        book_id: state.selectedBook.id,
        chapter_index: chapterIndex,
        position_seconds: positionSeconds,
      }),
    });
  } catch {
    // Fail silently to avoid interrupting playback.
  }
}

async function loadProgress() {
  if (!state.selectedBook) {
    return;
  }

  try {
    const progress = await apiRequest(`/api/v1/progress/${state.sessionId}/${state.selectedBook.id}`);
    chapterSelect.value = String(progress.chapter_index);
    setStatus(playerStatus, `Retomada detectada: capítulo ${progress.chapter_index + 1}`);
  } catch {
    setStatus(playerStatus, "Sem progresso anterior para este livro");
  }
}

async function addBookmark() {
  if (!state.selectedBook) {
    return;
  }
  const chapterIndex = Number(chapterSelect.value || 0);

  await apiRequest("/api/v1/bookmarks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: state.sessionId,
      book_id: state.selectedBook.id,
      chapter_index: chapterIndex,
      position_seconds: audio.currentTime || 0,
      note: "Marcador rapido",
    }),
  });

  await loadBookmarks();
}

async function loadBookmarks() {
  if (!state.selectedBook) {
    bookmarkList.innerHTML = "";
    return;
  }

  const bookmarks = await apiRequest(`/api/v1/bookmarks/${state.sessionId}/${state.selectedBook.id}`);
  bookmarkList.innerHTML = "";
  if (!bookmarks.length) {
    const item = document.createElement("li");
    item.textContent = "Sem bookmarks";
    bookmarkList.appendChild(item);
    return;
  }

  bookmarks.forEach((bookmark) => {
    const item = document.createElement("li");
    item.className = "bookmark-item";

    const button = document.createElement("button");
    button.textContent = `Cap. ${bookmark.chapter_index + 1} - ${Math.floor(bookmark.position_seconds)}s`;
    button.addEventListener("click", async () => {
      chapterSelect.value = String(bookmark.chapter_index);
      await loadChapterManifest();
      state.currentChunk = 0;
      await playCurrentChunk();
      audio.currentTime = bookmark.position_seconds;
    });

    item.appendChild(button);
    bookmarkList.appendChild(item);
  });
}

uploadBtn.addEventListener("click", async () => {
  if (!uploadInput.files || !uploadInput.files.length) {
    setStatus(uploadStatus, "Escolha um EPUB antes de enviar");
    return;
  }

  const formData = new FormData();
  formData.append("file", uploadInput.files[0]);

  try {
    setStatus(uploadStatus, "Enviando...");
    const response = await apiRequest("/api/v1/books/upload", {
      method: "POST",
      body: formData,
    });
    setStatus(uploadStatus, `Livro importado: ${response.title}`);
    await loadBooks();
  } catch (err) {
    setStatus(uploadStatus, `Falha no upload: ${err.message}`);
  }
});

chapterSelect.addEventListener("change", async () => {
  await loadChapterManifest();
  await saveProgress(Number(chapterSelect.value || 0), 0);
});

speedSelect.addEventListener("change", () => {
  audio.playbackRate = Number(speedSelect.value);
  localStorage.setItem("bookflix_speed", speedSelect.value);
});

voiceSave.addEventListener("click", () => {
  const value = voiceInput.value.trim();
  if (value) {
    localStorage.setItem("bookflix_voice", value);
    setStatus(playerStatus, `Voz preferida salva localmente: ${value}`);
  }
});

playBtn.addEventListener("click", async () => {
  try {
    await playCurrentChunk();
  } catch (err) {
    setStatus(playerStatus, `Erro ao reproduzir: ${err.message}`);
  }
});

pauseBtn.addEventListener("click", async () => {
  audio.pause();
  await saveProgress(Number(chapterSelect.value || 0), audio.currentTime || 0);
});

bookmarkBtn.addEventListener("click", async () => {
  try {
    await addBookmark();
  } catch (err) {
    setStatus(playerStatus, `Erro ao salvar bookmark: ${err.message}`);
  }
});

audio.addEventListener("ended", async () => {
  state.currentChunk += 1;
  await playCurrentChunk();
});

setInterval(() => {
  if (!audio.paused && state.selectedBook) {
    saveProgress(Number(chapterSelect.value || 0), audio.currentTime || 0);
  }
}, 15000);

(function boot() {
  const savedSpeed = localStorage.getItem("bookflix_speed");
  if (savedSpeed) {
    speedSelect.value = savedSpeed;
    audio.playbackRate = Number(savedSpeed);
  }
  voiceInput.value = localStorage.getItem("bookflix_voice") || "pt-BR-FranciscaNeural";

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => null);
  }

  loadBooks();
})();
