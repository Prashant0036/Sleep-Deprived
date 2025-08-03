async function getSearchSuggestions() {
  try {
    const response = await fetch('/search_suggestions_data/');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const suggestions = await response.json();
    return suggestions;
  } catch (error) {
    console.error('Error fetching search suggestions:', error);
    throw error; 
  }
}