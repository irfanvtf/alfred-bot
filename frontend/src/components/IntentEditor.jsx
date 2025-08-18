import React, { useState, useEffect } from "react";
import { Plus, X, Save, ArrowLeft, AlertCircle } from "lucide-react";

const IntentEditor = ({ intent, onSave, onCancel, language }) => {
  const [formData, setFormData] = useState({ ...intent });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    setFormData({ ...intent });
  }, [intent]);

  const validate = () => {
    const newErrors = {};

    if (!formData.id?.trim()) {
      newErrors.id = "Intent ID is required";
    }

    if (
      !formData.patterns ||
      formData.patterns.length === 0 ||
      formData.patterns.every((p) => !p.trim())
    ) {
      newErrors.patterns = "At least one pattern is required";
    }

    if (
      !formData.responses ||
      formData.responses.length === 0 ||
      formData.responses.every((r) => !r.text?.trim())
    ) {
      newErrors.responses = "At least one response is required";
    }

    if (!formData.metadata?.name?.trim()) {
      newErrors.name = "Name is required";
    }

    if (!formData.metadata?.category?.trim()) {
      newErrors.category = "Category is required";
    }

    if (!formData.metadata?.audience?.trim()) {
      newErrors.audience = "Audience is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleMetadataChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        [field]: value,
      },
    }));
  };

  const handlePatternChange = (index, value) => {
    const newPatterns = [...formData.patterns];
    newPatterns[index] = value;
    handleChange("patterns", newPatterns);
  };

  const handleResponseChange = (index, field, value) => {
    const newResponses = [...formData.responses];
    newResponses[index] = {
      ...newResponses[index],
      [field]: value,
    };
    handleChange("responses", newResponses);
  };

  const addPattern = () => {
    handleChange("patterns", [...formData.patterns, ""]);
  };

  const removePattern = (index) => {
    const newPatterns = [...formData.patterns];
    newPatterns.splice(index, 1);
    handleChange("patterns", newPatterns);
  };

  const addResponse = () => {
    handleChange("responses", [...formData.responses, { id: "", text: "" }]);
  };

  const removeResponse = (index) => {
    const newResponses = [...formData.responses];
    newResponses.splice(index, 1);
    handleChange("responses", newResponses);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      const updatedIntent = {
        ...formData,
        responses: formData.responses.map((response, index) => ({
          ...response,
          id: response.id || `${formData.id}_${index}`,
        })),
      };
      onSave(updatedIntent);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onCancel}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <h2 className="text-xl font-semibold text-gray-900">
              {intent.id ? "Edit Intent" : "Create New Intent"}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              <Save className="h-4 w-4" />
              Save Intent
            </button>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-8">
          {/* Basic Information */}
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">
              Basic Information
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label
                  htmlFor="intent-id"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Intent ID
                </label>
                <input
                  type="text"
                  id="intent-id"
                  value={formData.id || ""}
                  onChange={(e) => handleChange("id", e.target.value)}
                  className={`block w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors ${
                    errors.id
                      ? "border-red-300 bg-red-50"
                      : "border-gray-300 focus:border-indigo-500"
                  }`}
                  placeholder="e.g., greeting_hello"
                />
                {errors.id && (
                  <div className="flex items-center gap-1 mt-1 text-sm text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    {errors.id}
                  </div>
                )}
              </div>

              <div>
                <label
                  htmlFor="name"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.metadata?.name || ""}
                  onChange={(e) => handleMetadataChange("name", e.target.value)}
                  className={`block w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors ${
                    errors.name
                      ? "border-red-300 bg-red-50"
                      : "border-gray-300 focus:border-indigo-500"
                  }`}
                  placeholder="e.g., Hello Greeting"
                />
                {errors.name && (
                  <div className="flex items-center gap-1 mt-1 text-sm text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    {errors.name}
                  </div>
                )}
              </div>

              <div>
                <label
                  htmlFor="category"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Category
                </label>
                <input
                  type="text"
                  id="category"
                  value={formData.metadata?.category || ""}
                  onChange={(e) =>
                    handleMetadataChange("category", e.target.value)
                  }
                  className={`block w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors ${
                    errors.category
                      ? "border-red-300 bg-red-50"
                      : "border-gray-300 focus:border-indigo-500"
                  }`}
                  placeholder="e.g., Greeting"
                />
                {errors.category && (
                  <div className="flex items-center gap-1 mt-1 text-sm text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    {errors.category}
                  </div>
                )}
              </div>

              <div>
                <label
                  htmlFor="audience"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Audience
                </label>
                <input
                  type="text"
                  id="audience"
                  value={formData.metadata?.audience || ""}
                  onChange={(e) =>
                    handleMetadataChange("audience", e.target.value)
                  }
                  className={`block w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors ${
                    errors.audience
                      ? "border-red-300 bg-red-50"
                      : "border-gray-300 focus:border-indigo-500"
                  }`}
                  placeholder="e.g., general"
                />
                {errors.audience && (
                  <div className="flex items-center gap-1 mt-1 text-sm text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    {errors.audience}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Patterns */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">
              User Patterns
            </h3>
            <p className="text-sm text-gray-600">
              Add different ways users might express this intent. These are the
              phrases or questions users will ask.
            </p>

            <div className="space-y-3">
              {formData.patterns?.map((pattern, index) => (
                <div key={index} className="flex gap-3">
                  <input
                    type="text"
                    value={pattern}
                    onChange={(e) => handlePatternChange(index, e.target.value)}
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                    placeholder={`Pattern ${
                      index + 1
                    } (e.g., "Hello", "Hi there")`}
                  />
                  <button
                    type="button"
                    onClick={() => removePattern(index)}
                    className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}

              <button
                type="button"
                onClick={addPattern}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                <Plus className="h-4 w-4" />
                Add Pattern
              </button>

              {errors.patterns && (
                <div className="flex items-center gap-1 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  {errors.patterns}
                </div>
              )}
            </div>
          </div>

          {/* Responses */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">
              Bot Responses
            </h3>
            <p className="text-sm text-gray-600">
              Define how the bot should respond when this intent is detected.
              You can add multiple response variations.
            </p>

            <div className="space-y-4">
              {formData.responses?.map((response, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-gray-900">
                      Response {index + 1}
                    </h4>
                    <button
                      type="button"
                      onClick={() => removeResponse(index)}
                      className="text-red-600 hover:text-red-800 hover:bg-red-100 p-1 rounded transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Response ID (optional)
                      </label>
                      <input
                        type="text"
                        value={response.id || ""}
                        onChange={(e) =>
                          handleResponseChange(index, "id", e.target.value)
                        }
                        className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                        placeholder="Auto-generated if left empty"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Response Text
                      </label>
                      <textarea
                        rows={3}
                        value={response.text || ""}
                        onChange={(e) =>
                          handleResponseChange(index, "text", e.target.value)
                        }
                        className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none"
                        placeholder="Enter the bot's response text..."
                      />
                    </div>
                  </div>
                </div>
              ))}

              <button
                type="button"
                onClick={addResponse}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                <Plus className="h-4 w-4" />
                Add Response
              </button>

              {errors.responses && (
                <div className="flex items-center gap-1 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  {errors.responses}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntentEditor;
