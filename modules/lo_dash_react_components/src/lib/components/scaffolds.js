/*
  Unfinished code. Committing to branch to sync between devices.
  */


// A function that re-orders scaffolds to be in the same order as their associated problems
export function reorderScaffolds(problems, scaffolds) {
  // A helper function that returns the median of an array of numbers
  function median(array) {
    // Sort the array in ascending order
    array.sort((a, b) => a - b);
    // Find the middle index
    let mid = Math.floor(array.length / 2);
    // If the array has an odd length, return the middle element
    if (array.length % 2 === 1) {
      return array[mid];
    }
    // If the array has an even length, return the average of the middle two elements
    else {
      return (array[mid - 1] + array[mid]) / 2;
    }
  }

  // Annotate each scaffold with the indexes of the problems it's associated with
  for (let scaffold of scaffolds) {
    // Initialize an empty array to store the indexes
    scaffold.indexes = [];
    // Loop through the problems
    for (let i = 0; i < problems.length; i++) {
      // If the scaffold id is in the problem's scaffolds array, push the index to the scaffold's indexes array
      if (problems[i].scaffolds.includes(scaffold.id)) {
        scaffold.indexes.push(i);
      }
    }
  }

  // Take the median value of each scaffold's indexes array
  for (let scaffold of scaffolds) {
    // If the scaffold has no indexes, set its median to Infinity
    if (scaffold.indexes.length === 0) {
      scaffold.median = Infinity;
    }
    // Otherwise, use the helper function to calculate its median
    else {
      scaffold.median = median(scaffold.indexes);
    }
  }

  // Sort scaffolds by their median value in ascending order
  scaffolds.sort((a, b) => a.median - b.median);

  // Return the reordered scaffolds array
  return scaffolds;
}

// A function that re-orders scaffolds to be in the same order as their associated problems
function reorderScaffolds(problems, scaffolds) {
  // A helper function that returns the median of an array of numbers
  function median(array) {
    // Sort the array in ascending order
    array.sort((a, b) => a - b);
    // Find the middle index
    let mid = Math.floor(array.length / 2);
    // If the array has an odd length, return the middle element
    if (array.length % 2 === 1) {
      return array[mid];
    }
    // If the array has an even length, return the average of the middle two elements
    else {
      return (array[mid - 1] + array[mid]) / 2;
    }
  }

  // Annotate each scaffold with the indexes of the problems it's associated with
  for (let scaffold of scaffolds) {
    // Initialize an empty array to store the indexes
    scaffold.indexes = [];
    // Loop through the problems
    for (let i = 0; i < problems.length; i++) {
      // If the scaffold id is in the problem's scaffolds array, push the index to the scaffold's indexes array
      if (problems[i].scaffolds.includes(scaffold.id)) {
        scaffold.indexes.push(i);
      }
    }
  }

  // Take the median value of each scaffold's indexes array
  for (let scaffold of scaffolds) {
    // If the scaffold has no indexes, set its median to Infinity
    if (scaffold.indexes.length === 0) {
      scaffold.median = Infinity;
    }
    // Otherwise, use the helper function to calculate its median
    else {
      scaffold.median = median(scaffold.indexes);
    }
  }

  // Sort scaffolds by their median value in ascending order
  scaffolds.sort((a, b) => a.median - b.median);

  // Return the reordered scaffolds array
  return scaffolds;
}


// A function that checks if two arrays are equal
function arrayEqual(a, b) {
  // If the arrays have different lengths, return false
  if (a.length !== b.length) {
    return false;
  }
  // Loop through the elements of the arrays
  for (let i = 0; i < a.length; i++) {
    // If the elements are objects, recursively check their equality
    if (typeof a[i] === "object" && typeof b[i] === "object") {
      if (!arrayEqual(a[i], b[i])) {
        return false;
      }
    }
    // If the elements are not objects, compare them directly
    else {
      if (a[i] !== b[i]) {
        return false;
      }
    }
  }
  // If no difference is found, return true
  return true;
}

// A sample input for the problems array
let problems = [
  { id: "p1", scaffolds: ["s1", "s2", "s3"] },
  { id: "p2", scaffolds: ["s2", "s4"] },
  { id: "p3", scaffolds: ["s1", "s5"] },
  { id: "p4", scaffolds: ["s3", "s4", "s6"] },
];

// A sample input for the scaffolds array
let scaffolds = [
  { id: "s1" },
  { id: "s2" },
  { id: "s3" },
  { id: "s4" },
  { id: "s5" },
  { id: "s6" },
];

// A sample output for the reordered scaffolds array
let expected = [
  { id: "s1", indexes: [0, 2], median: 1 },
  { id: "s2", indexes: [0, 1], median: 0.5 },
  { id: "s3", indexes: [0, 3], median: 1.5 },
  { id: "s4", indexes: [1, 3], median: 2 },
  { id: "s5", indexes: [2], median: 2 },
  { id: "s6", indexes: [3], median: 3 },
];

// Call the reorderScaffolds function with the sample inputs
let actual = reorderScaffolds(problems, scaffolds);

// Check if the actual output matches the expected output using the arrayEqual function
console.log(arrayEqual(actual, expected)); // should print true
