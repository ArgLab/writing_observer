/**
 * This script defines functions for the hierarchical information area
 * of the common student errors dashboard.
 */
if (!window.dash_clientside) {
  window.dash_clientside = {}
}

window.dash_clientside.hierarchical_common_errors = {
  /**
   * Take the data returned from the LanguageTool and parse it
   * into the hierarchical format needed for the 3 types of graphs
   */
  populate_hierarchical_charts: function (data, toggleOrder) {
    const categoryCount = {}
    const subcategoryCount = {}
    const names = []
    const ids = []
    const parents = []
    const values = []
    const colors = []
    const order = (toggleOrder === 'stud-sub')
    for (let i = 0; i < data.length; i++) {
      for (const [key, value] of Object.entries(data[i].category_counts)) {
        categoryCount[key] = (categoryCount[key] || 0) + value
        if (order & value > 0) {
          names.push(data[i].profile.name.full_name)
          ids.push(`${key} - ${data[i].user_id}`)
          parents.push(key)
          values.push(value)
          colors.push('')
        }
      }
      for (const [key, value] of Object.entries(data[i].subcategory_counts)) {
        const keySplit = key.split(':')
        subcategoryCount[key] = (subcategoryCount[key] || 0) + value
        if (order & value > 0) {
          names.push(keySplit[1].trim())
          ids.push(`${key} -  - ${data[i].user_id}`)
          parents.push(`${keySplit[0]} - ${data[i].user_id}`)
          values.push(value)
          colors.push('')
        } else if (!order & value > 0) {
          names.push(data[i].profile.name.full_name)
          ids.push(`${data[i].user_id} - ${key}`)
          parents.push(key)
          values.push(value)
          colors.push('')
        }
      }
    }
    let total = 0

    const language = ['Grammar', 'Usage', 'Style', 'Semantics']
    const mechanics = ['Capitalization', 'Possible Typo', 'Punctuation', 'Spelling', 'Typography', 'Word Boundaries']

    for (const [key, value] of Object.entries(categoryCount)) {
      total = total + value
      if (language.includes(key)) {
        parents.push('Language')
      } else {
        parents.push('Mechanics')
      }
      names.push(key)
      ids.push(key)
      values.push(value)
      colors.push(categoryColors[key])
    }

    names.push('Language')
    ids.push('Language')
    const languageSum = language.reduce((acc, key) => {
      if (categoryCount.hasOwnProperty(key)) {
        return acc + categoryCount[key]
      }
      return acc
    }, 0)
    values.push(languageSum)
    colors.push('lightgray')
    parents.push('')

    names.push('Mechanics')
    ids.push('Mechanics')
    const mechanicsSum = mechanics.reduce((acc, key) => {
      if (categoryCount.hasOwnProperty(key)) {
        return acc + categoryCount[key]
      }
      return acc
    }, 0)
    values.push(mechanicsSum)
    colors.push('lightgray')
    parents.push('')

    if (!order) {
      for (const [key, value] of Object.entries(subcategoryCount)) {
        const keySplit = key.split(':')
        names.push(keySplit[1].trim())
        ids.push(key)
        parents.push(keySplit[0])
        values.push(value)
        colors.push('')
      }
    }

    const extendedData = [{ ids: [ids], labels: [names], parents: [parents], values: [values], 'marker.colors': [colors] }, [0], names.length]
    return [extendedData, extendedData, extendedData]
  }
}
