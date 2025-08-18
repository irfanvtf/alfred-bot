import React, { useState, useMemo } from "react";
import {
  Search,
  MessagesSquare,
  UsersRound,
  Plus,
  Filter,
  X,
} from "lucide-react";

const IntentList = ({ intents, loading, onEdit, onDelete, onCreate }) => {
  const [categoryFilter, setCategoryFilter] = useState("");
  const [audienceFilter, setAudienceFilter] = useState("");

  // Extract unique categories and audiences from intents
  const { categories, audiences } = useMemo(() => {
    if (!intents || intents.length === 0)
      return { categories: [], audiences: [] };

    const categories = [
      ...new Set(
        intents.map((intent) => intent.metadata?.category || "Uncategorized")
      ),
    ].sort();
    const audiences = [
      ...new Set(
        intents.map((intent) => intent.metadata?.audience || "general")
      ),
    ].sort();

    return { categories, audiences };
  }, [intents]);

  // Filter intents based on selected filters
  const filteredIntents = useMemo(() => {
    if (!intents) return [];

    return intents.filter((intent) => {
      const categoryMatch =
        !categoryFilter ||
        (intent.metadata?.category || "Uncategorized") === categoryFilter;
      const audienceMatch =
        !audienceFilter ||
        (intent.metadata?.audience || "general") === audienceFilter;
      return categoryMatch && audienceMatch;
    });
  }, [intents, categoryFilter, audienceFilter]);

  const clearFilters = () => {
    setCategoryFilter("");
    setAudienceFilter("");
  };

  const hasActiveFilters = categoryFilter || audienceFilter;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Intents</h2>
          <button
            onClick={onCreate}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            <Plus className="h-4 w-4" />
            Add Intent
          </button>
        </div>

        {/* Filters */}
        {(categories.length > 1 || audiences.length > 1) && (
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Filter className="h-4 w-4" />
              <span>Filter by:</span>
            </div>

            {categories.length > 1 && (
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-3 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="">All categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            )}

            {audiences.length > 1 && (
              <select
                value={audienceFilter}
                onChange={(e) => setAudienceFilter(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-3 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="">All audiences</option>
                {audiences.map((audience) => (
                  <option key={audience} value={audience}>
                    {audience}
                  </option>
                ))}
              </select>
            )}

            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                <X className="h-3 w-3" />
                Clear filters
              </button>
            )}

            <span className="text-sm text-gray-500">
              {filteredIntents.length} of {intents?.length || 0} intents
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      {filteredIntents && filteredIntents.length > 0 ? (
        <div className="divide-y divide-gray-100">
          {filteredIntents.map((intent) => (
            <div
              key={intent.id}
              className="px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              {/* Intent header */}
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900 truncate">
                  {intent.patterns && intent.patterns.length > 0
                    ? intent.patterns[0]
                    : intent.metadata.name}
                </h3>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {intent.metadata?.category || "Uncategorized"}
                </span>
              </div>

              {/* Intent details */}
              <div className="flex items-center gap-6 mb-3">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Search className="h-4 w-4" />
                  <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                    {intent.id}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <MessagesSquare className="h-4 w-4" />
                  <span>{intent.patterns?.length || 0} patterns</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <UsersRound className="h-4 w-4" />
                  <span>{intent.metadata?.audience || "general"}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => onEdit(intent)}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(intent.id)}
                  className="text-sm font-medium text-red-600 hover:text-red-800 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty state */
        <div className="px-6 py-12 text-center">
          <div className="mx-auto h-16 w-16 text-gray-400 mb-4">
            <MessagesSquare className="h-16 w-16" />
          </div>
          {hasActiveFilters ? (
            <>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No intents match your filters
              </h3>
              <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
                Try adjusting your filters or clear them to see all intents.
              </p>
              <button
                onClick={clearFilters}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 border border-indigo-300 hover:border-indigo-400 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                <X className="h-4 w-4" />
                Clear filters
              </button>
            </>
          ) : (
            <>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No intents yet
              </h3>
              <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
                Get started by creating your first intent. Intents help define
                what users are trying to accomplish.
              </p>
              <button
                onClick={onCreate}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                <Plus className="h-4 w-4" />
                Create Intent
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default IntentList;
