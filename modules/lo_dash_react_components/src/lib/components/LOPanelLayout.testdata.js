const testData = {
    id: "example",
    children: 'this is the main child',
    panels: [
        {children: 'boy panel', width: '25%', id: 'boy', side: 'left'},
        {children: 'girl panel', width: '14%', id: 'girl', side: 'left'},
        {children: 'dog panel', width: '11%', id: 'dog'},
        {children: 'cat panel', width: '18%', id: 'cat'}
    ],
    shown: ['cat', 'dog', 'girl']
}
export default testData;
