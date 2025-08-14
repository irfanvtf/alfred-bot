import React, { useState, useEffect } from 'react'

const IntentEditor = ({ intent, onSave, onCancel, language }) => {
  const [formData, setFormData] = useState({ ...intent })
  const [errors, setErrors] = useState({})

  useEffect(() => {
    setFormData({ ...intent })
  }, [intent])

  const validate = () => {
    const newErrors = {}

    if (!formData.id?.trim()) {
      newErrors.id = 'Intent ID is required'
    }

    if (!formData.patterns || formData.patterns.length === 0 || formData.patterns.every(p => !p.trim())) {
      newErrors.patterns = 'At least one pattern is required'
    }

    if (!formData.responses || formData.responses.length === 0 || formData.responses.every(r => !r.text?.trim())) {
      newErrors.responses = 'At least one response is required'
    }

    if (!formData.metadata?.category?.trim()) {
      newErrors.category = 'Category is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleMetadataChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        [field]: value
      }
    }))
  }

  const handlePatternChange = (index, value) => {
    const newPatterns = [...formData.patterns]
    newPatterns[index] = value
    handleChange('patterns', newPatterns)
  }

  const handleResponseChange = (index, field, value) => {
    const newResponses = [...formData.responses]
    newResponses[index] = {
      ...newResponses[index],
      [field]: value
    }
    handleChange('responses', newResponses)
  }

  const addPattern = () => {
    handleChange('patterns', [...formData.patterns, ''])
  }

  const removePattern = (index) => {
    const newPatterns = [...formData.patterns]
    newPatterns.splice(index, 1)
    handleChange('patterns', newPatterns)
  }

  const addResponse = () => {
    handleChange('responses', [...formData.responses, { id: '', text: '' }])
  }

  const removeResponse = (index) => {
    const newResponses = [...formData.responses]
    newResponses.splice(index, 1)
    handleChange('responses', newResponses)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      // Generate response IDs if they don't exist
      const updatedIntent = {
        ...formData,
        responses: formData.responses.map((response, index) => ({
          ...response,
          id: response.id || `${formData.id}_${index}`
        }))
      }
      onSave(updatedIntent)
    }
  }

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
        <h2 className="text-lg leading-6 font-medium text-gray-900">
          {intent.id ? 'Edit Intent' : 'Create New Intent'}
        </h2>
      </div>
      <form onSubmit={handleSubmit} className="px-4 py-5 sm:p-6">
        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
          <div className="sm:col-span-3">
            <label htmlFor="intent-id" className="block text-sm font-medium text-gray-700">
              Intent ID
            </label>
            <div className="mt-1">
              <input
                type="text"
                id="intent-id"
                value={formData.id}
                onChange={(e) => handleChange('id', e.target.value)}
                className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.id ? 'border-red-300' : ''}`}
              />
              {errors.id && <p className="mt-2 text-sm text-red-600">{errors.id}</p>}
            </div>
          </div>

          <div className="sm:col-span-3">
            <label htmlFor="category" className="block text-sm font-medium text-gray-700">
              Category
            </label>
            <div className="mt-1">
              <input
                type="text"
                id="category"
                value={formData.metadata?.category || ''}
                onChange={(e) => handleMetadataChange('category', e.target.value)}
                className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.category ? 'border-red-300' : ''}`}
              />
              {errors.category && <p className="mt-2 text-sm text-red-600">{errors.category}</p>}
            </div>
          </div>

          <div className="sm:col-span-3">
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700">
              Priority
            </label>
            <div className="mt-1">
              <select
                id="priority"
                value={formData.metadata?.priority || 1}
                onChange={(e) => handleMetadataChange('priority', parseInt(e.target.value))}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                  <option key={num} value={num}>{num}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="sm:col-span-6">
            <label className="block text-sm font-medium text-gray-700">
              Patterns
            </label>
            <div className="mt-1 space-y-2">
              {formData.patterns?.map((pattern, index) => (
                <div key={index} className="flex">
                  <input
                    type="text"
                    value={pattern}
                    onChange={(e) => handlePatternChange(index, e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => removePattern(index)}
                    className="ml-2 inline-flex items-center p-2 border border-transparent rounded-full shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={addPattern}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg className="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
                Add Pattern
              </button>
              {errors.patterns && <p className="mt-2 text-sm text-red-600">{errors.patterns}</p>}
            </div>
          </div>

          <div className="sm:col-span-6">
            <label className="block text-sm font-medium text-gray-700">
              Responses
            </label>
            <div className="mt-1 space-y-4">
              {formData.responses?.map((response, index) => (
                <div key={index} className="border border-gray-200 rounded-md p-4">
                  <div className="grid grid-cols-1 gap-y-4 gap-x-4 sm:grid-cols-6">
                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Response ID
                      </label>
                      <div className="mt-1">
                        <input
                          type="text"
                          value={response.id}
                          onChange={(e) => handleResponseChange(index, 'id', e.target.value)}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                    </div>
                    <div className="sm:col-span-6">
                      <label className="block text-sm font-medium text-gray-700">
                        Response Text
                      </label>
                      <div className="mt-1">
                        <textarea
                          rows={3}
                          value={response.text}
                          onChange={(e) => handleResponseChange(index, 'text', e.target.value)}
                          className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.responses ? 'border-red-300' : ''}`}
                        />
                      </div>
                    </div>
                    <div className="sm:col-span-6 flex justify-end">
                      <button
                        type="button"
                        onClick={() => removeResponse(index)}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      >
                        Remove Response
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              <button
                type="button"
                onClick={addResponse}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg className="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
                Add Response
              </button>
              {errors.responses && <p className="mt-2 text-sm text-red-600">{errors.responses}</p>}
            </div>
          </div>
        </div>

        <div className="mt-8 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Save
          </button>
        </div>
      </form>
    </div>
  )
}

export default IntentEditor