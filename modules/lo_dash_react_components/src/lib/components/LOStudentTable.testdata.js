/* eslint-disable no-magic-numbers */

const testData = {
  cards: [
    {
      id: '1',
      name: 'Alice',
      avatar: 'https://randomuser.me/api/portraits/women/68.jpg',
      columns: [
        { label: 'Essay Topic', value: 'The Importance of Sleep' },
        { label: 'Word Count', value: 1350 },
        { label: 'Writing Time', value: '2 hours 15 mins' },
        { label: 'Grade', value: 'A' },
        { label: 'Comments', value: 'Excellent work!' },
        { label: 'Sources Used', value: 3, tooltip: "Stanford Medicine: Sleep\nNational Sleep Foundation\nSleep Foundation" },
        { label: 'Late Submission', value: false },
      ],
      color: 'lightblue',
    },
    {
      id: '2',
      name: 'Bob',
      avatar: 'https://randomuser.me/api/portraits/men/12.jpg',
      columns: [
        { label: 'Essay Topic', value: 'The Ethics of AI' },
        { label: 'Word Count', value: 1675 },
        { label: 'Writing Time', value: '3 hours 20 mins' },
        { label: 'Grade', value: 'B' },
        { label: 'Comments', value: 'Good effort.' },
        { label: 'Sources Used', value: 2, tooltip: "Wired\nTechTalks\n" },
        { label: 'Late Submission', value: true },
      ],
      color: 'lightgreen',
    },
    {
      id: '3',
      name: 'Charlie',
      avatar: 'https://randomuser.me/api/portraits/men/44.jpg',
      columns: [
        { label: 'Essay Topic', value: 'Climate Change and Society' },
        { label: 'Word Count', value: 1200 },
        { label: 'Writing Time', value: '2 hours 5 mins' },
        { label: 'Grade', value: 'B+' },
        { label: 'Comments', value: 'Good effort, but could use more research.' },
        { label: 'Sources Used', value: 2, tooltip: "NASA\nNOAA\n" },
        { label: 'Late Submission', value: false },
      ],
      color: 'pink',
    },
    {
      id: '4',
      name: 'David',
      avatar: 'https://randomuser.me/api/portraits/men/22.jpg',
      columns: [
        { label: 'Essay Topic', value: 'The Future of Work' },
        { label: 'Word Count', value: 1400 },
        { label: 'Writing Time', value: '2 hours 30 mins' },
        { label: 'Grade', value: 'A-' },
        { label: 'Comments', value: 'Great work, keep it up!' },
        { label: 'Sources Used', value: 4, tooltip: "Wikipedia: Future of Work\nMcKinsey\nDeloitte\nForbes\n" },
        { label: 'Late Submission', value: false },
      ],
      color: 'lightyellow',
    }
  ],
  controlGroups: [
    {
      id: 'group1',
      title: 'Student Grouping',
      options: ['Topic', 'Grade', 'Writing Time'],
      selectedOption: 'Writing Time'
    },
    {
      id: 'group2',
      title: 'View',
      options: ['Overview', 'Progress', 'Scoring'],
      selectedOption: 'Overview'
    }
  ]
};

export default testData;
