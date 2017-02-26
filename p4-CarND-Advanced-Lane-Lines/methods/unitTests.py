

def testFindPoints():
    """
    Purpose: Test find points function.
    Inputs: findPoints.findPoints() and hardcoded calibration path
    Outputs: Prints points and success message if program reaches end.

    """

    from calibration import findPoints

    imagesPath = "../camera_cal/calibration*.jpg"

    objpoints, imgpoints = findPoints.findPoints(imagesPath)

    print("objpoints", objpoints, "\n")
    print("imgpoints", imgpoints, "\n")

    return print("Success")

# testFindPoints()


def testCalibration():
    """
    Purpose: Test calibration function.
    Inputs: findPoints.findPoints(), calibrate.calibrate(),
    hardcoded calibration path, hard coded image path.
    Outputs: Success message if program reaches end.

    """

    from calibration import findPoints
    imagesPath = "../camera_cal/calibration*.jpg"
    objpoints, imgpoints = findPoints.findPoints(imagesPath)

    from calibration import calibrate
    import matplotlib.image as mpimg
    image = mpimg.imread('../test_images/test1.jpg')
    #image = "test"
    ret, mtx, dist, rvecs, tvecs = calibrate.calibrate(
        image, objpoints, imgpoints)

    return print("Success")

# testCalibration()


def testDrawChessBoardCorners():
    """
    Purpose:
    Inputs: 
    Outputs: 
    """

    from calibration import findPoints
    imagesPath = "../camera_cal/calibration*.jpg"
    objpoints, imgpoints = findPoints.findPoints(imagesPath)

    from calibration import calibrate
    import matplotlib.image as mpimg
    image = mpimg.imread('../camera_cal/calibration12.jpg')
    ret, mtx, dist, rvecs, tvecs = calibrate.calibrate(
        image, objpoints, imgpoints)

    from distortionCorrection import undistort

    nx = 9  # the number of inside corners in x
    ny = 6  # the number of inside corners in y

    undistort, src, dst, ret, corners = undistort.chessBoardTest(
        image, nx, ny, mtx, dist)

    # Draw corners
    import cv2
    chessBoard = cv2.drawChessboardCorners(undistort, (nx, ny), corners, ret)

    # Plot results
    import matplotlib.pyplot as plt
    f, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 9))
    f.tight_layout()
    ax1.imshow(image)
    ax1.set_title('Original Image', fontsize=50)
    ax2.imshow(chessBoard)
    ax2.set_title('Chessboard corners', fontsize=50)
    plt.subplots_adjust(left=0., right=1, top=0.9, bottom=0.)

    plt.show()

    return "success"

# testDrawChessBoardCorners()


def testUndistort():
    """
    Purpose:
    Inputs: 
    Outputs: 
    """

    from calibration import findPoints
    imagesPath = "../camera_cal/calibration*.jpg"
    objpoints, imgpoints = findPoints.findPoints(imagesPath)

    import matplotlib.image as mpimg
    image = mpimg.imread('../test_images/test1.jpg')

    from calibration import calibrate
    ret, mtx, dist, rvecs, tvecs = calibrate.calibrate(
        image, objpoints, imgpoints)

    from distortionCorrection import undistort
    undistort, src, dst = undistort.birdsEyeView(image, mtx, dist)

    import matplotlib.pyplot as plt
    f, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 9))
    f.tight_layout()
    ax1.imshow(image)
    ax1.set_title('Original image', fontsize=50)
    ax2.imshow(undistort)
    ax2.set_title('Undistorted image', fontsize=50)
    plt.subplots_adjust(left=0., right=1, top=0.9, bottom=0.)

    plt.show()

    return "success"

# testUndistort()


def testBirdsEyeView():
    """
    Purpose:
    Inputs: 
    Outputs: 
    """

    from calibration import findPoints
    imagesPath = "../camera_cal/calibration*.jpg"
    objpoints, imgpoints = findPoints.findPoints(imagesPath)

    import matplotlib.image as mpimg
    image = mpimg.imread('../test_images/test5.jpg')

    from calibration import calibrate
    ret, mtx, dist, rvecs, tvecs = calibrate.calibrate(
        image, objpoints, imgpoints)

    from distortionCorrection import undistort
    undistort, src, dst = undistort.birdsEyeView(image, mtx, dist)

    print(src)

    from perspectiveTransform import perspectiveTransform
    transformMatrix, warpedImage = perspectiveTransform.perspectiveTransform(
        image, src, dst)

    import matplotlib.pyplot as plt
    f, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 9))
    f.tight_layout()
    ax1.imshow(image)
    ax1.set_title('Original image', fontsize=50)
    ax2.imshow(warpedImage)
    ax2.set_title('Birds eye image', fontsize=50)
    plt.subplots_adjust(left=0., right=1, top=0.9, bottom=0.)

    plt.show()

    return "success"

# testBirdsEyeView()


def testThresholds():
    """
    Purpose:
    Inputs: 
    Outputs: 
    """

    from calibration import findPoints
    imagesPath = "../camera_cal/calibration*.jpg"
    objpoints, imgpoints = findPoints.findPoints(imagesPath)

    import matplotlib.image as mpimg
    image = mpimg.imread('../test_images/test5.jpg')

    from calibration import calibrate
    ret, mtx, dist, rvecs, tvecs = calibrate.calibrate(
        image, objpoints, imgpoints)

    from distortionCorrection import undistort
    undistort, src, dst = undistort.birdsEyeView(image, mtx, dist)

    from perspectiveTransform import perspectiveTransform
    transformMatrix, warpedImage = perspectiveTransform.perspectiveTransform(
        image, src, dst)

    from colorGradientThreshold import absoluteSobelThreshold, directionThreshold, magnitudeThreshold, hlsSelect
    import numpy as np

    image = undistort

    ksize = 21

    # Apply each of the thresholding functions
    gradx = absoluteSobelThreshold.abs_sobel_thresh(
        image, orient='x', sobel_kernel=ksize, thresh=(30, 90))

    grady = absoluteSobelThreshold.abs_sobel_thresh(
        image, orient='y', sobel_kernel=ksize, thresh=(30, 90))

    mag_binary = magnitudeThreshold.mag_thresh(
        image, sobel_kernel=ksize, mag_thresh=(30, 90))

    dir_binary = directionThreshold.dir_threshold(
        image, sobel_kernel=15, thresh=(0.7, 1.3))

    hls_select = hlsSelect.hlsSelect(image)

    combined = np.zeros_like(dir_binary)
    combined[((gradx == 1) & (grady == 1)) | (
        (mag_binary == 1) & (dir_binary == 1)) | (hls_select == 1)] = 1

    import matplotlib.pyplot as plt
    f, (ax1, ax2, ax3, ax4, ax5, ax6, ax7) = plt.subplots(
        1, 7, figsize=(24, 9))
    f.tight_layout()

    ax1.imshow(image)
    ax1.set_title('Original', fontsize=30)

    ax2.imshow(gradx, cmap="gray")
    ax2.set_title('gradx', fontsize=30)

    ax3.imshow(grady, cmap="gray")
    ax3.set_title('grady', fontsize=30)

    ax4.imshow(mag_binary, cmap="gray")
    ax4.set_title('mag_binary', fontsize=30)

    ax5.imshow(dir_binary, cmap="gray")
    ax5.set_title('dir_binary', fontsize=30)

    ax6.imshow(combined, cmap="gray")
    ax6.set_title('Combined', fontsize=30)

    ax7.imshow(hls_select, cmap="gray")
    ax7.set_title('hls_select', fontsize=30)

    plt.subplots_adjust(left=0., right=1, top=0.9, bottom=0.)
    plt.show()

    plt.imshow(combined, cmap="gray")
    plt.show()

    return "success"


testThresholds()