// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // 初始化日期选择器
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        input.valueAsDate = new Date();
    });

    // 添加健康记录表单提交
    var addRecordForm = document.querySelector('#addRecordModal form');
    if (addRecordForm) {
        addRecordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // TODO: 实现表单提交逻辑
            var modal = bootstrap.Modal.getInstance(document.querySelector('#addRecordModal'));
            modal.hide();
            showAlert('success', '记录添加成功！');
        });
    }

    // 删除记录按钮点击事件
    var deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (confirm('确定要删除这条记录吗？')) {
                // TODO: 实现删除记录逻辑
                showAlert('success', '记录删除成功！');
            }
        });
    });
});

// 显示提示信息
function showAlert(type, message) {
    var alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);

    // 3秒后自动关闭
    setTimeout(function() {
        alertDiv.remove();
    }, 3000);
}

// 更新健康目标进度
function updateProgress(elementId, value) {
    var progressBar = document.querySelector(`#${elementId} .progress-bar`);
    if (progressBar) {
        progressBar.style.width = `${value}%`;
        progressBar.setAttribute('aria-valuenow', value);
    }
}

// 图表初始化（示例）
function initCharts() {
    // TODO: 使用图表库（如Chart.js）实现数据可视化
    console.log('Charts initialized');
}

// 表单验证
function validateForm(form) {
    var inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    var isValid = true;

    inputs.forEach(function(input) {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// 响应式导航栏处理
var navbarToggler = document.querySelector('.navbar-toggler');
if (navbarToggler) {
    navbarToggler.addEventListener('click', function() {
        document.querySelector('.navbar-collapse').classList.toggle('show');
    });
} 