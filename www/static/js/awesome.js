// user js

// extend jquery
$(document).ready(function () {
    $.fn.extend({
        showFormError: function (err) {
            return this.each(function () {
                let $form = $(this);
                if (! $form.is('form')){
                    return console.error('Invalid call of showFormError on non-form element.');
                }
                // reset form danger
                $form.find('uk-form-danger').removeClass('uk-form-danger');
                // alert info
                let $alert = $form.find('.uk-alert'),
                    field = err && err.data;
                if ($alert.length < 1){
                    return console.warn('No .uk-alert element found.');
                }
                if(err){
                    $alert.text(err.msg? err.msg : err.error? err.error : err).removeClass('uk-hidden').show();
                    let alertTop = $alert.offset().top - 60;
                    if(alertTop < $(window).scrollTop){
                        $('html, body').animate({scrollTop: alertTop});
                    }
                    if(field){
                        $form.find('[name=' + field + ']').addClass('uk-form-danger');
                    }
                }
                else{
                    $alert.text('').addClass('uk-hidden').hide();
                }
            });
        },
        
        showFormLoading: function (isLoading=true) {
            return this.each(function () {
                let $form = $(this),
                    $button = $form.find('button'),
                    $icon = $button.filter('[type="submit"]').find('i');
                if (! $form.is('form')){
                    return console.error('Invalid call of showFormLoading on non-form element.');
                }
                if(isLoading){
                    $button.addClass('disabled');
                    $icon.addClass('uk-icon-spinner uk-icon-spin');
                }
                else{
                    $button.removeClass('disabled');
                    $icon.removeClass('uk-icon-spinner uk-icon-spin');
                }

            });
        },
        
        postJson: function (url, data, callback) {
            return this.each(function () {

            });
        }
    });
});
