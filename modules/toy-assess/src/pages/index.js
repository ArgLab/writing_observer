import path from 'path';

// @refresh reset

export default function Home( { pages, text } ) {
  console.log(pages);
  return (
    <>
      <h1> Pages </h1>
      <p> We have many more than committed here, including math problems, SBAs, etc. We are leaving one demo for now, since the rest are externally contributed and may have IP issues. </p>
      <ul>
        { pages.map((page) => <li> <a href={ page.url }> { page.title } </a> </li>) }
      </ul>
      <pre>{ JSON.stringify(text) }</pre>
    </>
  );
}


export async function getStaticProps() {
  function fullPagePath(shortname) {
    return path.join(directoryPath, shortname, 'page.js');
  }
  function description(shortname) {
    const fileContent = fs.readFileSync(fullPagePath(shortname), 'utf8');
    const firstLine = fileContent.split('\n')[0];
    const comment = firstLine.split("//").slice(1).join('//').trim();
    if(comment === "") {
      return shortname;
    }
    return comment;
  }

  const fs = require('fs');
  const directoryPath = path.join(process.cwd(), 'src/app');
  const allFiles = fs.readdirSync(directoryPath);
  const directories = allFiles.filter(fileName => {
    const fullPath = path.join(directoryPath, fileName);
    return fs.statSync(fullPath).isDirectory();
  });
  const directoriesWithPageJs = directories.filter(directory => {
    const filesInDirectory = fs.readdirSync(path.join(directoryPath, directory));
    return filesInDirectory.includes('page.js');
  });
  const pages = directoriesWithPageJs.map(url => ({
    title: description(url),
    url: url
  }));

  console.log(directoryPath);
  //const pages = [{title: "Text style changer demo", url: "/changer"}];
  const text = pages;
  return {
    props: {
      pages,
      text
    }
  };
}
