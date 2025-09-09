import { FC } from 'react';
import Typewriter from 'typewriter-effect';

const migrationScenarios = [
  "I am an Indian software engineer with a job offer in Berlin...",
  "I got accepted to TUM in Munich and need to move in 5 months...",
  "I'm a Brazilian professional moving to Portugal with my family...",
  "I received a Blue Card offer from a company in Netherlands...",
  "I'm a student from China accepted to a Master's program in Sweden..."
];

const TypewriterHero: FC = () => {
  return (
    <div className="max-w-4xl mx-auto text-center py-20">
      <h1 className="text-4xl font-bold text-gray-900 mb-6">
        Plan Your Migration Journey
      </h1>
      <div className="text-xl text-gray-600 h-24 flex items-center justify-center">
        <span className="mr-2">Tell us your story:</span>
        <Typewriter
          onInit={(typewriter) => {
            typewriter
              .typeString(migrationScenarios[0])
              .pauseFor(2000)
              .deleteAll()
              .typeString(migrationScenarios[1])
              .pauseFor(2000)
              .deleteAll()
              .typeString(migrationScenarios[2])
              .pauseFor(2000)
              .deleteAll()
              .typeString(migrationScenarios[3])
              .pauseFor(2000)
              .deleteAll()
              .typeString(migrationScenarios[4])
              .pauseFor(2000)
              .deleteAll()
              .start();
          }}
        />
      </div>
    </div>
  );
};

export default TypewriterHero;
