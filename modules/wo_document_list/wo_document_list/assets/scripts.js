/**
 * General scripts used for the document list dashboard
 */

if (!window.dash_clientside) {
  window.dash_clientside = {}
}

/**
 * Create a list item with a link to the document
 */
const createDocLink = function (doc) {
  return {
    namespace: 'dash_html_components',
    type: 'Li',
    props: {
      children: {
        namespace: 'dash_html_components',
        type: 'A',
        props: { children: doc.title, href: `https://docs.google.com/document/d/${doc.id}/edit`, target: '_blank' }
      }
    }
  }
}

/**
 * Create a student card that lists the various types of documents (latest, tagged, assignments)
 */
const createDocStudentCard = function (student) {
  console.log(student)
  const header = {
    namespace: 'dash_bootstrap_components',
    type: 'CardHeader',
    props: { children: student.profile.name.full_name }
  }
  const latest = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: [
        { namespace: 'dash_html_components', type: 'H6', props: { children: 'Latest doc' } },
        { namespace: 'dash_html_components', type: 'A', props: { children: student.latest ? createDocLink(student.latest) : {} } }
      ]
    }
  }
  const assignment = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: [
        { namespace: 'dash_html_components', type: 'H6', props: { children: 'Assignment Docs' } },
        { namespace: 'dash_html_components', type: 'Ul', props: { children: student.assignment_docs?.map(function (doc) { return createDocLink(doc) }) || [] } }
      ]
    }
  }
  const tagged = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: [
        { namespace: 'dash_html_components', type: 'H6', props: { children: 'Tagged docs' } },
        { namespace: 'dash_html_components', type: 'Ul', props: { children: student.tagged_docs?.map(function (doc) { return createDocLink(doc) }) || [] } }
      ]
    }
  }
  const card = {
    namespace: 'dash_bootstrap_components',
    type: 'Card',
    props: { children: [header, latest, assignment, tagged] }
  }
  return {
    namespace: 'dash_bootstrap_components',
    type: 'Col',
    props: { children: card, width: 4 }
  }
}

// These are the nodes we want on the communication protocol
const ENDPOINTS = ['latest_doc_ids', 'tagged_docs_per_student', 'assignment_docs']

window.dash_clientside.document_list = {
  /**
   * Fetch assignments for a given class and populate the radio items with them
   */
  fetch_assignments: async function (hash) {
    if (hash.length === 0) { return window.dash_clientside.no_update }
    const decoded = decode_string_dict(hash.slice(1))
    if (!decoded.course_id) { return window.dash_clientside.no_update }
    const response = await fetch(`${window.location.protocol}//${window.location.hostname}:${window.location.port}/google/course_work/${decoded.course_id}`)
    const data = await response.json()
    const options = data.courseWork.map(function (item) {
      return { label: item.title, value: item.id }
    })
    return options
  },

  /**
   * Send data to the communication protocol
   */
  send_to_loconnection: async function (state, hash, tag, assignment) {
    if (state === undefined) {
      return window.dash_clientside.no_update
    }
    if (state.readyState === 1) {
      if (hash.length === 0) { return window.dash_clientside.no_update }
      const decoded = decode_string_dict(hash.slice(1))
      if (!decoded.course_id) { return window.dash_clientside.no_update }

      decoded.assignment_id = assignment || ''

      decoded.tag_path = tag ? `tags.${tag}` : 'tags'

      const message = {
        wo: {
          execution_dag: 'writing_observer',
          target_exports: ENDPOINTS, // this needs to be latest doc, tag docs, and assignment docs
          kwargs: decoded
        }
      }
      return JSON.stringify(message)
    }
    return window.dash_clientside.no_update
  },

  /**
   * Update the student grid based on the response from the websocket
   * We iterate over each of the endpoint's results to create a new array
   * where each item is a student and their corresponding documents of
   * each type.
   * Lastly, we feed this new array into into the createStudentDocCard.
   */
  update_student_grid: function (data) {
    const studentMap = new Map()
    for (const key of ENDPOINTS) {
      if (Array.isArray(data[key])) {
        for (const student of data[key]) {
          const id = student.user_id
          if (!id) { continue }
          if (!studentMap.has(id)) {
            studentMap.set(id, { user_id: id, profile: student.profile })
          }
          const studentData = studentMap.get(id)
          if (key === 'latest_doc_ids') {
            studentData.latest = student.doc_id ? { id: student.doc_id, title: student.doc_id } : {}
          } else if (key === 'tagged_docs_per_student') {
            studentData.tagged_docs = student.documents?.map(function (doc) {
              return { title: doc.title, id: doc.id }
            }) || []
          } else if (key === 'assignment_docs') {
            studentData.assignment_docs = student.documents?.map(function (doc) {
              return { title: doc.title, id: doc.id }
            }) || []
          }
        }
      }
    }
    const gridObjects = Array.from(studentMap.values()).map(function (student) {
      return createDocStudentCard(student)
    })
    return gridObjects
  }
}
