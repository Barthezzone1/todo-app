import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [username, setUsername] = useState("");
  const [apiKey, setApiKey] = useState(localStorage.getItem("apiKey") || "");
  const [todos, setTodos] = useState([]);
  const [newTitle, setNewTitle] = useState("");
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // Po starcie – jeśli mamy apiKey w localStorage, pobierz todo + statsy
  useEffect(() => {
    if (apiKey) {
      fetchTodos();
      fetchStats();
    }
  }, [apiKey]);

  const register = async (e) => {
    e.preventDefault();
    if (!username.trim()) {
      alert("Podaj nazwę użytkownika");
      return;
    }
    try {
      const res = await axios.post(`${API_URL}/register`, {
        username: username.trim(),
      });
      const data = res.data;
      setApiKey(data.api_key);
      localStorage.setItem("apiKey", data.api_key);
      alert(`Zarejestrowano jako ${data.username}. API key zapisany.`);
      setUsername("");
      await fetchTodos();
      await fetchStats();
    } catch (err) {
      console.error("Błąd rejestracji:", err.response?.status, err.response?.data || err.message);
      alert("Błąd rejestracji. Sprawdź backend (logi w konsoli).");
    }
  };

  const getAuthHeaders = () => {
    return apiKey
      ? {
          headers: {
            "X-API-Key": apiKey, // WAŻNE: to musi się zgadzać z backendem
          },
        }
      : {};
  };

  const fetchTodos = async () => {
    if (!apiKey) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/todos`, getAuthHeaders());
      setTodos(res.data);
    } catch (err) {
      console.error(
        "Błąd pobierania zadań:",
        err.response?.status,
        err.response?.data || err.message
      );
      alert("Błąd pobierania zadań (sprawdź apiKey i backend).");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!apiKey) return;
    try {
      const res = await axios.get(`${API_URL}/stats`, getAuthHeaders());
      setStats(res.data);
    } catch (err) {
      console.error(
        "Błąd pobierania statystyk:",
        err.response?.status,
        err.response?.data || err.message
      );
    }
  };

  const addTodo = async (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const res = await axios.post(
        `${API_URL}/todos`,
        { title: newTitle.trim() },
        getAuthHeaders()
      );
      setNewTitle("");
      setTodos((prev) => [...prev, res.data]);
      await fetchStats();
    } catch (err) {
      console.error("Błąd tworzenia zadania:", err.response?.status, err.response?.data || err.message);
      alert("Błąd tworzenia zadania.");
    }
  };

  const toggleTodo = async (id, done) => {
    try {
      const res = await axios.put(
        `${API_URL}/todos/${id}`,
        { done: !done },
        getAuthHeaders()
      );
      setTodos((prev) => prev.map((t) => (t.id === id ? res.data : t)));
      await fetchStats();
    } catch (err) {
      console.error("Błąd aktualizacji zadania:", err.response?.status, err.response?.data || err.message);
      alert("Błąd aktualizacji zadania.");
    }
  };

  const deleteTodo = async (id) => {
    try {
      await axios.delete(`${API_URL}/todos/${id}`, getAuthHeaders());
      setTodos((prev) => prev.filter((t) => t.id !== id));
      await fetchStats();
    } catch (err) {
      console.error("Błąd usuwania zadania:", err.response?.status, err.response?.data || err.message);
      alert("Błąd usuwania zadania.");
    }
  };

  const clearApiKey = () => {
    setApiKey("");
    localStorage.removeItem("apiKey");
    setTodos([]);
    setStats(null);
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: 16, fontFamily: "sans-serif" }}>
      <h1>Todo App (FastAPI + React)</h1>

      {/* Sekcja rejestracji / API key */}
      <section
        style={{
          border: "1px solid #ccc",
          padding: 12,
          borderRadius: 8,
          marginBottom: 16,
        }}
      >
        <h2>1. Rejestracja / API key</h2>
        {!apiKey ? (
          <form onSubmit={register}>
            <label>
              Nazwa użytkownika:
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{ marginLeft: 8 }}
              />
            </label>
            <button type="submit" style={{ marginLeft: 8 }}>
              Zarejestruj
            </button>
          </form>
        ) : (
          <div>
            <p>
              <strong>API key:</strong> {apiKey}
            </p>
            <button onClick={clearApiKey}>Wyloguj / usuń API key</button>
          </div>
        )}
      </section>

      {/* Sekcja zadań */}
      <section
        style={{
          border: "1px solid #ccc",
          padding: 12,
          borderRadius: 8,
          marginBottom: 16,
        }}
      >
        <h2>2. Twoje zadania</h2>

        {!apiKey && <p>Najpierw zarejestruj się, aby pobrać API key.</p>}

        {apiKey && (
          <>
            <button onClick={fetchTodos} disabled={loading}>
              Odśwież listę
            </button>

            <form onSubmit={addTodo} style={{ marginTop: 12 }}>
              <input
                type="text"
                placeholder="Nowe zadanie..."
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                style={{ marginRight: 8 }}
              />
              <button type="submit">Dodaj</button>
            </form>

            {loading && <p>Ładowanie...</p>}

            <ul style={{ marginTop: 12 }}>
              {todos.map((todo) => (
                <li key={todo.id} style={{ marginBottom: 4 }}>
                  <label>
                    <input
                      type="checkbox"
                      checked={todo.done}
                      onChange={() => toggleTodo(todo.id, todo.done)}
                      style={{ marginRight: 8 }}
                    />
                    {todo.title}
                  </label>
                  <button
                    onClick={() => deleteTodo(todo.id)}
                    style={{ marginLeft: 8 }}
                  >
                    Usuń
                  </button>
                </li>
              ))}
            </ul>

            {todos.length === 0 && !loading && <p>Brak zadań.</p>}
          </>
        )}
      </section>

      {/* Statystyki */}
      <section
        style={{
          border: "1px solid #ccc",
          padding: 12,
          borderRadius: 8,
        }}
      >
        <h2>3. Statystyki</h2>
        {stats ? (
          <ul>
            <li>Łącznie: {stats.total}</li>
            <li>Zrobione: {stats.done}</li>
            <li>Do zrobienia: {stats.not_done}</li>
          </ul>
        ) : (
          <p>Brak danych (zarejestruj się i dodaj zadania).</p>
        )}
      </section>
    </div>
  );
}

export default App;