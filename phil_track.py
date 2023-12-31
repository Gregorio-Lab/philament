from math import sqrt
import numpy as np
import trackpy as tp
import os
import os.path
import cv2

import pandas as pd
import tifffile as tif
from pims import PyAVVideoReader


# This function creates a dictionary containing row names for the output DF, which will then be transposed into column names.
# The Key is the row number, and the definition is always the same for the first 5 elements
# The elements >5 are just the time in seconds that have passed since the beginning of the recording
def column_naming(df_length, file_fps):
    df_dict = {
        0: "Particle",
        1: "FirstX",
        2: "FirstY",
        3: "First_Frame",
        4: "Displacement",
    }
    recip_fps = 1 / file_fps

    # This loop writes the intervals between frames in seconds.
    # For a 5fps movie, 10 sec long, the intervals will be in 1/5fps (0.2) seconds
    # and will contain 50 cells (the calculation on line 28 is just getting the time passed, starting with 0.2 + 0.2 = 0.4)
    for cell in range(5, df_length):
        df_dict[cell] = recip_fps
        # f"{round(recip_fps,1)} (s)"  ## I'm putting this code here incase I want to implement this later but as of now, I know this is just going to be a pain
        recip_fps += 1 / file_fps

    return df_dict


# Apologies if this is overdocumentation
"""
tracking_data_analysis
Inputs:
split_list -> nested lists containing the filepaths for preprocessed .tif image sequences
progress -> int used for progress bar window
root -> tk root of progress bar window
settings -> dict containing the user defined parameters, such as search radius and tracking memory
name_indices -> tuple containing the negative indices of the file number, to keep track of which video the analyzed data came from

            Workflow
--------------------------------
1. for (loop) number of conditions

    a. create/clear dataframes which will contain all the positional data

    b. for (loop) file in condition
        * increase progress bar by 1 (since it starts at 0)
        * separate filename and filenumber
        * read .avi/.tif files (is_avi = True/False respectively) 

        * trackpy batch track and link objects
        * sort datapoints by particle and frame
        * separate out unwanted data (only frame, x, y, and particle #)

        * for (loop) objects in tracked file
            - find first/last x & y values (.iloc) 
            - calculate total displacement travelled (pythagorean equation)
            - save first frame, first x/y, and particle number with displacement

            - for (loop) # of frames object is tracked
                > calculate distances travelled and speed from frame to frame (pythag. equation)
                > append value to list & repeat
            
            - combine speed df and positional info df
            - add to condition file
        
        * save condition file with all movies data 

        * for (loop) objects in tracked file
            - calculate avg and std of object size

        * join object size and condition file together
        * add to output dataframe with all the other data in that condition
    
    c. save .CSV file with data from all files in the condition 
    

"""


def tracking_data_analysis(
    split_list, progress, root, settings, name_indices, is_avi, path_img_dir
):
    # Forcing matplotlib to use "Agg" instead of Tk for the path creation
    # Otherwise this raises a RuntimeError
    if settings["paths"]:
        import matplotlib

        matplotlib.use("Agg")

        from matplotlib.pyplot import savefig, subplots, close

        # Used this for messing with paths figures
        # import matplotlib.pyplot as plt

    caught_exceptions = ""

    # This is for changing the superimposed image
    """
    stacked_image = cv2.imread(
        "C:\\Users\\panch\\Desktop\\Important\\Gregorio Lab\\Final Philament Paper\\FIGURE-Paths-V3\\100ugMyosin Paths\\ZProjections\\ZProjection-100ugMyosin06.tif"
    )
    """

    # To make the analysis easier, this file will give a quick glimpse, ie. condition A is faster than condition B
    summary_file = {
        "Condition": [],
        "# of Files": [],
        "Average Speed": [],
        "Speed SEM": [],
        "Total # of Objects": [],
    }

    # Tracking the objects & saving to csv file (does i .tif/avi videos at a time, specified by sheet_size)
    for j in range(0, len(split_list)):
        # Defining Variables / Clearing Dataframes
        full_obj_df = pd.DataFrame()
        final_df = pd.DataFrame()

        for i in range(0, len(split_list[j])):
            displacement_df = pd.DataFrame()

            progress.set(progress.get() + 1)
            root.update()

            # Specifing which movie the data came from
            filename = os.path.basename(split_list[j][i])
            file_num = int(filename[name_indices[0] : name_indices[1]])

            obj_size_list = []

            if is_avi == True:
                frames = PyAVVideoReader(split_list[j][i])

                avi_array = []
                for x in range(0, len(frames)):
                    avi_array.append(cv2.cvtColor(frames[x], cv2.COLOR_BGR2GRAY))
                frames = avi_array

            else:
                frames = tif.imread(split_list[j][i])

            # tracking the objects & collecting obj information like position, size, brightness, ect.
            f = tp.batch(
                frames[:],
                settings["object_area"],
                invert=True,
                engine="numba",
                processes="auto",
            )

            # Linking the objects / tracking their paths
            try:
                linked_obj = tp.link_df(
                    f, settings["search_range"], memory=settings["trk_memory"]
                )
            except Exception as e:
                caught_exceptions += f"{filename[7 : name_indices[0]]}{file_num} was skipped due to:\n{e}\n"
                continue

            linked_obj = linked_obj.sort_values(by=["particle", "frame"])

            if settings["paths"] == True:
                # Creating Path images for files!
                fig, ax = subplots()
                paths_fig = tp.plot_traj(linked_obj, ax=ax, superimpose=frames[0])
                # This line below is how kwargs are passed to plt.plot, so you can change the line thicknesses
                # plot_style={"linewidth": 0.50, "color": "red"})

                # Saving to Path folder
                path_name = os.path.join(
                    path_img_dir, f"{filename[:name_indices[1]]}.png"
                )

                # Options/ ways to save the figures without the axes
                # plt.axis("off")
                # savefig(path_name, bbox_inches="tight", pad_inches=0, dpi=150)

                savefig(path_name, dpi=150)

                # Make sure to empty memory after saving plots
                close()

            # This next section is getting the speed and positional data about the objects
            # The data is formatted as follows (example data):
            #
            # 1st X | 1st Y | First Frame | Displacement |{reciprocal_fps} * 1 | {reciprocal_fps} * 2 | {reciprocal_fps} * 3 | ect..
            # ---------------------------------------------------------------------------------------------------------
            #  150  |  150  |      0      |     18.6     |These sections are the instantaneous speed of the object at each frame
            #  200  |  200  |      0      |     8.2      |  1.2 (Microns/sec)  |          2.3         |            0.5       |
            #  168  |  15   |      2      |     1.55     |         0.3         |          0.8         |            1.2       |

            # dd_values stands for desired_displacement values
            dd_values = linked_obj[["particle", "frame", "x", "y"]]
            total_objs = dd_values["particle"].iloc[-1]
            reciprocol_fps = 1 / settings["fps"]

            # The workflow for this loop is to separate the data for each particle into a new dataframe, then
            # find the initial object coordinates & first frame (so you can go back and locate the object).
            #
            # Then for each frame, the object positions and frame numbers are used to find the change in distance
            # from frame to frame. This is converted to an instantaneous velocity by multiplying by
            # the pixel size and dividing by the reciprocol fps, and this number is appended to the list.

            for particle in range(0, total_objs):
                pythag_df = dd_values[dd_values["particle"] == particle]

                if len(pythag_df) > 1:
                    first_x = pythag_df["x"].iloc[0]
                    first_y = pythag_df["y"].iloc[0]
                    first_frame = pythag_df["frame"].iloc[0]
                    particle_num = pythag_df["particle"].iloc[0]
                    last_x = pythag_df["x"].iloc[-1]
                    last_y = pythag_df["y"].iloc[-1]

                    # In plain english, this is pythagorean theorem, (a^2 + b^2) = c^2,
                    # where a and b are the x and y distances travelled between frame n and frame n+1

                    displacement = (
                        sqrt(((first_x - last_x) ** 2) + (first_y - last_y) ** 2)
                        * settings["pixel_size"]
                    )
                    output_list = [
                        particle_num,
                        first_x,
                        first_y,
                        first_frame,
                        displacement,
                    ]

                    for frame in range(1, len(pythag_df)):
                        Xn = pythag_df["x"].iloc[frame - 1]
                        Yn = pythag_df["y"].iloc[frame - 1]
                        Frame_n = pythag_df["frame"].iloc[frame - 1]

                        Xn1 = pythag_df["x"].iloc[frame]
                        Yn1 = pythag_df["y"].iloc[frame]
                        Frame_n1 = pythag_df["frame"].iloc[frame]

                        frame_diff = Frame_n1 - Frame_n

                        displacement = sqrt(((Xn - Xn1) ** 2) + (Yn - Yn1) ** 2)
                        displacement = (displacement * settings["pixel_size"]) / (
                            reciprocol_fps * frame_diff
                        )

                        output_list.append(displacement)

                    output_list_df = pd.DataFrame(output_list)
                    displacement_df = pd.concat(
                        [displacement_df, output_list_df], axis=1
                    )

                # This removes particles only detected for a single frame
                else:
                    pass

            # By using the dictionary retuned in column_naming() this line renames the rows of the data frame
            # which is then transposed and set as the column names
            displacement_df = displacement_df.rename(
                index=column_naming(len(displacement_df), settings["fps"])
            )

            displacement_df = displacement_df.transpose()

            # when avg_speed_lamba is called, it inserts a column, so the speeds are shifted one to the right
            # this is why the row slicing points increase by 1
            avg_speed_lambda = lambda row: np.nanmean(row[6:])
            std_speed_lambda = lambda row: np.nanstd(row[7:])
            path_length_lambda = lambda row: np.sum(row[8:] * reciprocol_fps)

            displacement_df.insert(
                0,
                "File",
                file_num,
                allow_duplicates=True,
            )

            displacement_df.insert(
                5,
                "Avg Speed",
                displacement_df.apply(avg_speed_lambda, axis=1),
            )

            displacement_df.insert(
                6,
                "Speed Std",
                displacement_df.apply(std_speed_lambda, axis=1),
            )

            displacement_df.insert(
                7, "Path Length", displacement_df.apply(path_length_lambda, axis=1)
            )

            displacement_df = displacement_df.reset_index(drop=True)

            # Full object data option where all variables are saved (object x and y for each frame & object, lots of data!)
            if settings["full_obj_data"] == True:
                df2 = linked_obj
                df2.insert(0, "File", file_num, allow_duplicates=True)
                full_obj_df = pd.concat([full_obj_df, df2])

            # This section is finding the # of pixels that are in each of the object (object size)
            desired_values = linked_obj[["frame", "particle", "mass"]]
            total_objs = desired_values["particle"].iloc[-1]

            # This is how the obj_size DataFrame is formatted for the size of objects and file information
            # Average Obj Size | Std of Obj Size | File | Particle |
            # ----------------------------------------------------------
            #       14.86      |       7.38      |   1  |     0    |
            #       33.33      |       9.24      |   1  |     1    |
            #       55.06      |       5.18      |   1  |     2    |
            #       ect...     |       ect...    |ect...|   ect... |

            # Loop to calculate mean and std for the particle size * brightness,
            # which is converted into pixels by particle size/255
            for object in range(0, int(total_objs)):
                mass_df = desired_values[desired_values["particle"] == object]

                # If just one data point is available, obj is skipped, since you cant take a std from one data point
                if len(mass_df) > 1:
                    avg_mass = (mass_df["mass"].mean()) / 255
                    mass_std = (mass_df["mass"].std()) / 255

                    # Adding the mean and stdev of the object size to list
                    size_list = [avg_mass.round(2), mass_std.round(2)]
                    obj_size_list.append(size_list)

                else:
                    pass

            obj_size_df = pd.DataFrame(
                obj_size_list, columns=["Avg_Obj_Size", "Std_Obj_Size"]
            )

            # This is joining the two dataframes together, for the final/ output DataFrame
            output_df = obj_size_df.join(displacement_df)

            # What's happening in the .join() line:
            # Average Obj Size | Std of Obj Size |  +  | File | Particle | 1st X | 1st Y | First Frame |  Avg Speed   | Speed Std | Displacement |{reciprocal_fps} * 1 | {reciprocal_fps} * 2 | {reciprocal_fps} * 3 |
            # -----------------------------------|  +  |-----------------------------------------------------------------------------------------------------------------------------------------------------------------
            #       14.86      |       7.38      |  +  |   1  |     0    |  150  |  150  |      0      |      2.5     |   3.342   |     18.6     |These sections are the instantaneous speed of the object at each frame
            #       33.33      |       9.24      |  +  |   1  |     1    |  200  |  200  |      0      |      6.1     |   0.069   |     8.2      |  1.2 (Microns/sec)  |          2.3         |            0.5       |
            #       55.06      |       5.18      |  +  |   1  |     2    |  168  |  15   |      2      |      0.5     |   0.420   |     1.55     |         0.3         |          0.8         |            1.2       |
            #       ect...     |       ect...    |  +  |ect...|   ect... | ect...| ect...|    ect...   |     ect...   |   ect...  |    ect...    |       ect...        |         ect...       |           ect...     |

            final_df = pd.concat([final_df, output_df])

        # Put in calculations for average speeds (for files as well as conditions, maybe summary file) #todo
        filename = os.path.basename(split_list[j][0])
        proper_name = filename[7 : name_indices[0]]

        # With the final DF finished, calculations for summary files start
        file_speeds = np.array(final_df.iloc[:, 8:])

        summary_file["Condition"].append(proper_name)
        summary_file["# of Files"].append(i + 1)
        summary_file["Average Speed"].append(np.nanmean(file_speeds))
        summary_file["Speed SEM"].append(np.nanstd(file_speeds) / sqrt(len(final_df)))
        summary_file["Total # of Objects"].append(len(final_df))

        final_df.to_csv(f"{proper_name}.csv", index=0)

        # Full object data option
        if settings["full_obj_data"] == True:
            full_obj_df.to_csv(f"{proper_name}-Full Object Data.csv")

    summary_df = pd.DataFrame.from_dict(summary_file)
    summary_df.to_csv("Summary.csv", index=0)

    return caught_exceptions
