/**
 * This is a two-column display, showing problems and their related scaffolds.
 */

import React, { useEffect, useLayoutEffect, useRef } from 'react';

import PropTypes from 'prop-types';
import { PieChart, Pie, Cell, Label } from 'recharts';
import { Arrow, initArrows, updateArrowPositions, stagger, djb2 } from './helperlib';

const studentPropType = {
  initials: PropTypes.string.isRequired,
  problem: PropTypes.string.isRequired,
  scaffold: PropTypes.string,
  id: PropTypes.string.isRequired,
};

const studentsPropType = PropTypes.arrayOf(PropTypes.shape(studentPropType));

const problemPropType = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  id: PropTypes.string.isRequired,
  relatedScaffolds: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  students: studentsPropType,
  zones: PropTypes.shape({[PropTypes.string]: PropTypes.number}),
};

const problemsPropType = PropTypes.arrayOf(PropTypes.shape(problemPropType));

const scaffoldPropType = {
  id: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  students: studentsPropType,
};

const scaffoldsPropType = PropTypes.arrayOf(PropTypes.shape(scaffoldPropType));

/**
 * Add a count and index to each object in the input data array based on a given field.
 *
 * We use this so that we can count (1) how many students are working on each problem (2) give
 * each of them a unique position within (0, count), so we can space them nicely.
 *
 * Args:
 *   data (list): A list of objects.
 *   field (str): A string representing the field to be used for counting and indexing.
 *
 * Returns:
 *   list: A new list of objects, where each object has an additional "count" and "index" key.
 *   The "count" value represents the total number of objects in the input data array that have the same
 *   value for the field, and the "index" value represents the index of the object among that subset of objects.
 */
function addCountAndIndex(data, field) {
  const counts = {};
  let indexedData = data.map((obj) => {
    const fieldValue = obj[field];
    if (fieldValue in counts) {
      counts[fieldValue]++;
    } else {
      counts[fieldValue] = 0;
    }
    return { ...obj, index: counts[fieldValue] };
  });
  indexedData = indexedData.map((obj) => {
    const fieldValue = obj[field];
    return { ...obj, count: counts[fieldValue] + 1 };
  });
  return indexedData;
}

/*
 * This function takes in a list of students, scaffolds, and problems and annotates each scaffold and problem with the list of students working on them.
 *
 * This should probably be a function which is called twice, once for problems and once for scaffolds, taking
 * a generic 'items,' eventually.
 *
 * This will pass over items which already have lists of associated students, as we expect will eventually come from our reducers (but not for our test data)
 *
 * Args:
 *  students (list): A list of dictionaries containing information about each student.
 *  scaffolds (list): A list of dictionaries containing information about each scaffold.
 *  problems (list): A list of dictionaries containing information about each problem.
 *
 * Returns:
 *   None. This function modifies the scaffolds and problems lists in place by adding a 'students' field to each dictionary with the list of students working on the scaffold or problem.
 */
function annotateWithStudents(students, scaffolds, problems) {
  for (const scaffold of scaffolds) {
    if(scaffold.students) {
      continue;
    }
    scaffold.students = [];
    for (const student of students) {
      if (student.scaffold === scaffold.id) {
        scaffold.students.push(student);
      }
    }
  }
  for (const problem of problems) {
    if(problem.students) {
      continue;
    }    problem.students = [];
    for (const student of students) {
      if (student.problem === problem.id) {
        problem.students.push(student);
      }
    }
  }
}


/**
 * A card representing a single problem.
 */
function Problem({ id, title, description, students, zones }) {
  /* Dummy data. We'll bring in real data later. */
  const pie_chart_data = Object.entries(zones).map(([name, value]) => ({name, value}));

  console.log(zones);
  const totalStudents = students.length;

  const colors = {
    none: 'var(--none-color)',
    znd: 'var(--fail-color)',
    zpd: 'var(--zpd-color)',
    zad: 'var(--mastery-color)',
  };

  return (
    <div id={'problem-' + id} className="card problem">
      <div style={{ display: 'flex' }}>
        <div style={{ flex: 1, marginRight: '10px' }}>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        <div style={{ width: '80px', height: '80px' }}>
          <PieChart width={80} height={80}>
            <Pie
              data={pie_chart_data}
              dataKey="value"
              nameKey="name"
              innerRadius={20}
              outerRadius={40}
              isanimation={false}
            >
              {pie_chart_data.map((entry) => {
                console.log(colors[entry.name]);
                return (
                <Cell
                  key={entry.name}
                  fill={colors[entry.name]}
                />
              )})}
              <Label value={`${totalStudents}`} position="center" />
            </Pie>
          </PieChart>
        </div>
      </div>
      <div className="initials-box" id={'initials-problem-' + id}></div>
    </div>
  );
}

Problem.propTypes = problemPropType;

/**
 * A card representing a single scaffold
 */
function Scaffold({ id, title, description }) {
  return (
    <div id={'scaffold-' + id} className="card scaffold">
      <div className="target-box" id={'initials-target-' + id}></div>
      <div className="scaffold-content">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

Scaffold.propTypes = scaffoldPropType;

/**
 * A hidden box with circles for all the students in absolute
 * positions. Students will be placed in the appropriate problems with
 * JavaScript.
 */
function Students({ students }) {
  useEffect(() => {
    function moveStudents() {
      const index_students = addCountAndIndex(students, 'problem');
      index_students.forEach((student) => {
        const targetBox = document.querySelector(
          `#${`initials-problem-${student.problem}`}`
        );
        // const sourceBox = document.querySelector('#student-container');
        // const sourceRect = sourceBox.getBoundingClientRect();
        const studentCircle = document.querySelector(`#${student.id}`);

        const targetRect = targetBox.getBoundingClientRect();
        const studentRect = studentCircle.getBoundingClientRect();
        const top =
          targetRect.top - studentRect.height / 2 + targetRect.height / 2  + window.scrollY;
        const left =
          targetRect.left -
          studentRect.width / 2 +
          targetRect.width * stagger(student.index, student.count) + window.scrollX;
        studentCircle.style.position = 'absolute';
        studentCircle.style.top = `${top}px`;
        studentCircle.style.left = `${left}px`;
      });
    }
    moveStudents();
    window.addEventListener('resize', moveStudents);
    return () => {
      window.removeEventListener('resize', moveStudents);
    };
  }, [students]);

  return (
    <div className="students" id="student-container">
      {students.map((student) => (
        <div
          className="student-initials"
          data-target={'initials-problem-' + student.problem}
          id={student.id}
          key={student.id}
        >
          {student.initials}
        </div>
      ))}
    </div>
  );
}

Students.propTypes = {
  students: studentsPropType.isRequired
};

/**
 * A spacer div, so we have room for arrows and curves connecting problems
 * to scaffolds.
 */
function Connectors() {
  return <div className="connectors" />;
}

/**
 * A zero-sized div for all the arrows. These are absolute positioned objects which
 * we move out of the div with JavaScript.
 */
function Arrows({ students }) {
  useLayoutEffect(() => {
    updateArrowPositions();
  }, []);

  const arrows = [];

  students.forEach((student) => {
    const { id, scaffold } = student;
    if (scaffold) {
      const scaffoldId = 'initials-target-' + scaffold;
      arrows.push(
        <Arrow
          key={"arrow_"+id}
          source={id}
          target={scaffoldId}
        />
      );
    }
  });

  return <div className="arrow-wrapper" id="arrow-wrapper">{arrows}</div>;
}

Arrows.propTypes = {
  students: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    initials: PropTypes.string.isRequired,
    problem: PropTypes.string.isRequired
  })).isRequired
};

Arrows.propTypes = {
  students: studentsPropType.isRequired
};

/**
 * We draw connectors on this background
 */
function BackgroundCanvas({ problems }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    function renderCanvas() {
      context.clearRect(0, 0, canvas.width, canvas.height);
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      context.translate(-rect.left, -rect.top);

      // We really need something like this:
      //
      // canvas.width = document.documentElement.scrollWidth;
      // canvas.height = document.documentElement.scrollHeight;
      // context.translate(-window.pageXOffset, -window.pageYOffset);
      //
      // But it doesn't work since scaling is wrong, and the canvas doesn't
      // fill the full document in CSS.

      // Now you can draw on the canvas using ClientRect coordinates
      context.lineWidth = 6;
      for (const problem of problems) {
        for (const scaffold of problem.relatedScaffolds) {
          context.beginPath();
          const problem_element = document.getElementById(
            'problem-' + problem.id
          );
          const scaffold_element = document.getElementById(
            'scaffold-' + scaffold
          );
          const problem_rect = problem_element.getBoundingClientRect();
          const scaffold_rect = scaffold_element.getBoundingClientRect();

          const startX = problem_rect.right;
          const startY = problem_rect.top + problem_rect.height / 2;
          const endX = scaffold_rect.left;
          const endY = scaffold_rect.top + scaffold_rect.height / 2;

          const control1X = startX + (endX - startX) / 2;
          const control1Y = startY;
          const control2X = control1X;
          const control2Y = endY;

          context.moveTo(startX, startY);
          context.bezierCurveTo(
            control1X,
            control1Y,
            control2X,
            control2Y,
            endX,
            endY
          );
          const gradient = context.createLinearGradient(startX, 0, endX, 0);
          const degreesInCircle = 360;
          const problem_hash = djb2(problem.id) % degreesInCircle;
          const scaffold_hash = djb2(scaffold) % degreesInCircle;
          gradient.addColorStop(0, `hsl(${problem_hash}, 56%, 80%)`);
          gradient.addColorStop(1, `hsl(${scaffold_hash}, 56%, 80%)`);
          context.strokeStyle = gradient;
          context.stroke();
        }
      }
    }
    renderCanvas();
    window.addEventListener('resize', renderCanvas);
    window.addEventListener('scroll', renderCanvas);

    return () => {
      window.removeEventListener('resize', renderCanvas);
      window.removeEventListener('scroll', renderCanvas);
    };
  }, []);

  return <canvas ref={canvasRef} className="background-canvas" />;
}

BackgroundCanvas.propTypes ={
  problems: problemsPropType.isRequired
};

/**
 * This is the main display. It's a subcomponent, since the top-level component
 * has a bunch of statically-positioned helper divs for students, arrows, and
 * background.
 */
function Container({ problems, scaffolds }) {
  return (
    <div className="container">
      <div className="problem-container">
        {problems.map((problem, index) => (
          <Problem key={index} {...problem} />
        ))}
      </div>
      <Connectors />
      <div className="scaffold-container">
        {scaffolds.map((scaffold, index) => (
          <Scaffold key={index} {...scaffold} />
        ))}
      </div>
    </div>
  );
}

Container.propTypes ={
  problems: problemsPropType.isRequired,
  scaffolds: scaffoldsPropType.isRequired
};

/**
 * The DAProblemDisplay component is responsible for displaying
 * information about students, problems, and scaffolds. It takes in an
 * array of student objects, each containing their initials, the
 * problem they are working on, the scaffold they are using (if any),
 * and their unique ID.
 *
 * It renders which scaffolds associate with which problems, and which
 * scaffolds or problems students are currently using.
 */
class DAProblemDisplay extends React.Component {
  render() {
    const { students, problems, scaffolds } = this.props;
    annotateWithStudents(students, scaffolds, problems);

    return (
      <div className="App" id="problem-page-wrapper">
        {/*<Arrows students={students} />*/}
        <Container problems={problems} scaffolds={scaffolds} />
        <Students students={students} />
        <BackgroundCanvas problems={problems} />
      </div>
    );
  }
}

DAProblemDisplay.propTypes = {
  /**
   * students (array): An array of objects containing information about each student:
   * - initials (string): The student's initials.
   * - problem (string): The ID of the problem the student is working on.
   * - scaffold (string): The ID of the scaffold the student is using (if any).
   * - id (string): The unique ID of the student.
   */
  students: PropTypes.arrayOf(
    PropTypes.shape({
      initials: PropTypes.string.isRequired,
      problem: PropTypes.string.isRequired,
      scaffold: PropTypes.string,
      id: PropTypes.string.isRequired,
    })
  ).isRequired,
  /**
   * problems (array): An array of objects containing information about each problem:
   * - title (string): The title of the problem.
   * - description (string): A description of the problem.
   * - id (string): The unique ID of the problem.
   * - relatedScaffolds (array): An array of strings representing the IDs of scaffolds related to the problem.
   */
  problems: PropTypes.arrayOf(PropTypes.shape({
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    id: PropTypes.string.isRequired,
    relatedScaffolds: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  })).isRequired,
  /**
   * scaffolds (array): An array of objects containing information about each scaffold:
   * - id (string): The unique ID of the scaffold.
   * - title (string): The title of the scaffold.
   * - description (string): A description of the scaffold.
   * - content (string): The content of the scaffold.
   */
  scaffolds: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
  })).isRequired,};

initArrows();

export default DAProblemDisplay;
