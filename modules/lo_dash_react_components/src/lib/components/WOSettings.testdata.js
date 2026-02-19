
const testData = {
  options: [
    { id: 'a1', label: 'A1', parent: 'a' },
    { id: 'a2', types: { highlight: {}, metric: {} }, label: 'A2', parent: 'a' },
    { id: 'a1a', types: { highlight: {}, metric: {} }, label: 'A1A', parent: 'a1' },
    { id: 'a', label: 'A', parent: '' },
    { id: 'b', types: { highlight: {}, metric: {} }, label: 'B', parent: '' },
    { id: 'c', types: { highlight: {}, metric: {} }, label: 'C', parent: '' }
  ]
};

export default testData;
