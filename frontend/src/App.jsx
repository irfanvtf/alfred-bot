import React, { useState, useEffect } from "react";
import IntentList from "./components/IntentList";
import IntentEditor from "./components/IntentEditor";
import LanguageSelector from "./components/LanguageSelector";

function App() {
  const [language, setLanguage] = useState("en");
  const [intents, setIntents] = useState([]);
  const [selectedIntent, setSelectedIntent] = useState(null);
  const [isNewIntent, setIsNewIntent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch intents when language changes
  useEffect(() => {
    const fetchIntents = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/v1/cms/intents/${language}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch intents: ${response.status}`);
        }
        const data = await response.json();
        setIntents(data.intents || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchIntents();
  }, [language]);

  const handleCreateIntent = () => {
    setSelectedIntent({
      id: "",
      patterns: [""],
      responses: [{ id: "", text: "" }],
      metadata: {
        name: "",
        category: "",
        audience: "",
        tags: [],
      },
    });
    setIsNewIntent(true);
  };

  const handleEditIntent = (intent) => {
    setSelectedIntent(intent);
    setIsNewIntent(false);
  };

  const handleSaveIntent = async (intent) => {
    setLoading(true);
    setError(null);
    try {
      const method = isNewIntent ? "POST" : "PUT";
      const url = isNewIntent
        ? `/api/v1/cms/intents/${language}`
        : `/api/v1/cms/intents/${language}/${intent.id}`;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(intent),
      });

      if (!response.ok) {
        throw new Error(`Failed to save intent: ${response.status}`);
      }

      // Refresh the intents list
      const refreshResponse = await fetch(`/api/v1/cms/intents/${language}`);
      if (!refreshResponse.ok) {
        throw new Error(`Failed to refresh intents: ${refreshResponse.status}`);
      }
      const data = await refreshResponse.json();
      setIntents(data.intents || []);
      setSelectedIntent(null);
      setIsNewIntent(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteIntent = async (intentId) => {
    if (!window.confirm("Are you sure you want to delete this intent?")) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/v1/cms/intents/${language}/${intentId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to delete intent: ${response.status}`);
      }

      // Refresh the intents list
      const refreshResponse = await fetch(`/api/v1/cms/intents/${language}`);
      if (!refreshResponse.ok) {
        throw new Error(`Failed to refresh intents: ${refreshResponse.status}`);
      }
      const data = await refreshResponse.json();
      setIntents(data.intents || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Chatbot CMS</h1>
          <LanguageSelector
            language={language}
            onLanguageChange={setLanguage}
          />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedIntent ? (
          <IntentEditor
            intent={selectedIntent}
            onSave={handleSaveIntent}
            onCancel={() => {
              setSelectedIntent(null);
              setIsNewIntent(false);
            }}
            language={language}
          />
        ) : (
          <IntentList
            intents={intents}
            loading={loading}
            onEdit={handleEditIntent}
            onDelete={handleDeleteIntent}
            onCreate={handleCreateIntent}
          />
        )}
      </main>
    </div>
  );
}

export default App;
