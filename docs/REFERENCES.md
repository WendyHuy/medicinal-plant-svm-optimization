# Tài liệu tham khảo

Nguồn chính thức kiểm tra trong nghiên cứu 27–28/10/2026. Số liệu dự án lấy từ log, không lấy từ các bài dưới đây.

1. Islam, S. và cộng sự (2023). BDMediLeaves, bản 6 loài. Mendeley Data V1. https://data.mendeley.com/datasets/t9rns2gmr3/1 · DOI 10.17632/t9rns2gmr3.1 · CC BY 4.0.
2. Bergstra, J., Bengio, Y. (2012). Random Search for Hyper-Parameter Optimization. JMLR 13, 281–305. https://jmlr.org/papers/v13/bergstra12a.html
3. Optuna 4.5.0. TPESampler API. https://optuna.readthedocs.io/en/v4.5.0/reference/samplers/generated/optuna.samplers.TPESampler.html
4. scikit-learn. RBF SVM parameters. https://scikit-learn.org/stable/auto_examples/svm/plot_rbf_parameters.html
5. scikit-learn. Common pitfalls and recommended practices. https://scikit-learn.org/stable/common_pitfalls.html
6. scikit-learn. Nested versus non-nested cross-validation. https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html
7. scikit-image 0.25.x. Local Binary Pattern for texture classification. https://scikit-image.org/docs/0.25.x/auto_examples/features_detection/plot_local_binary_pattern.html
8. scikit-image 0.25.x. GLCM Texture Features. https://scikit-image.org/docs/0.25.x/auto_examples/features_detection/plot_glcm.html
9. scikit-image 0.25.x. Histogram of Oriented Gradients. https://scikit-image.org/docs/0.25.x/auto_examples/features_detection/plot_hog.html
10. Diwedi và cộng sự. Công trình CNN và SVM tối ưu cho cây dược liệu, Multimedia Tools and Applications (2024). DOI 10.1007/s11042-023-16733-8. https://link.springer.com/article/10.1007/s11042-023-16733-8 · Dùng mô tả/tóm tắt nhà xuất bản để nhận diện hướng liên quan; không so điểm trực tiếp do khác dữ liệu/giao thức.

Dự án không thực hiện nested CV hoàn chỉnh. Dùng một holdout tách khỏi lựa chọn và CV trên development. CV sau chọn mô hình có thiên lệch lạc quan; test chỉ có ý nghĩa trong giới hạn dữ liệu đã nêu.
