import { Element } from "react-scroll";
import { details, features } from "../constants/index.jsx"; // Keep original import path, assuming it's JSX
import React from 'react'; // Import React

// Define interfaces for the data structures imported from constants/index.jsx
// These types describe the shape of the objects within your 'features' and 'details' arrays.
interface FeatureItem {
  id: number | string; // Assuming 'id' can be a number or string
  icon: string;
  caption: string;
  title: string;
  text: string;
}

interface DetailItem {
  id: number | string; // Assuming 'id' can be a number or string
  icon: string;
  title: string;
}

// Ensure the 'features' and 'details' arrays are typed correctly based on the interfaces
// Note: In a real project, you might define these types directly in constants/index.ts
// and then import them here, along with the data.
// For this conversion, we're defining the types here and assuming the data
// imported from constants/index.jsx conforms to these types.
const typedFeatures: FeatureItem[] = features as FeatureItem[]; // Type assertion
const typedDetails: DetailItem[] = details as DetailItem[];     // Type assertion


const Features: React.FC = () => {
  return (
    <section>
      <Element name="features">
        <div className="container mx-auto px-4 py-16">
          <div className="relative flex md:flex-wrap flex-nowrap border-2 border-s3 rounded-7xl md:overflow-hidden max-md:flex-col feature-after md:g7 max-md:border-none max-md:rounded-none max-md:gap-3">
            {/* Use the type-asserted features array */}
            {typedFeatures.map(({ id, icon, caption, title, text }) => (
              <div
                key={id}
                className="relative z-2 md:px-10 px-5 md:pb-10 pb-5 flex-50 max-md:g7 max-md:border-2 max-md:border-s3 max-md:rounded-3xl max-md:flex-320"
              >
                <div className="w-full flex justify-start items-start">
                  <div className="-ml-3 mb-12 flex items-center justify-center flex-col">
                    <div className="w-0.5 h-16 bg-s3" />

                    <img
                      src={icon}
                      className="size-28 object-contain"
                      alt={title} // Added alt for accessibility
                    />
                  </div>
                </div>

                <p className="caption mb-5 max-md:mb-6">{caption}</p>
                <h2 className="max-w-400 mb-7 h3 text-p4 max-md:mb-6 max-md:h5">
                  {title}
                </h2>
                <p className="mb-11 body-1 max-md:mb-8 max-md:body-3">{text}</p>
              </div>
            ))}

            <ul className="relative flex justify-around flex-grow px-[5%] border-2 border-s3 rounded-7xl max-md:hidden">
              <div className="absolute bg-s3/20 top-[38%] left-0 right-0 w-full h-[1px] z-10" />

              {/* Use the type-asserted details array */}
              {typedDetails.map(({ id, icon, title }) => (
                <li key={id} className="relative pt-16 px-4 pb-14">
                  <div className="absolute top-8 bottom-0 left-1/2 bg-s3/20 w-[1px] h-full z-10" />

                  <div className="flex items-center justify-center mx-auto mb-3 border-2 border-s2 rounded-full hover:border-s4 transition-all duration-500 shadow-500 size-20">
                    <img
                      src={icon}
                      alt={title} // Added alt for accessibility
                      className="size-17/20 object-contain z-20"
                    />
                  </div>

                  <h3 className="relative z-2 max-w-36 mx-auto my-0 base-small text-center uppercase">
                    {title}
                  </h3>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Element>
    </section>
  );
};

export default Features;