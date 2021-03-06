// user js

// extend Number, transfer to Date as seconds.
if (! Number.prototype.toDate) {
    Number.prototype.toDate = function () {
        return new Date(this * 1000); // js is ms. python is s.
    }
}

// extend Date, format to str.
// yyyy/yy  mm/m  dd/d  HH/H  MM/M  SS/S  II/I  p/P  a/A/ac  b/B
if (! Date.prototype.formatStr) {
    Date.prototype.formatStr = function (fmtStr) {
        fmtStr = fmtStr || 'yyyy-mm-dd HH:MM';
        let code = /[a-zA-Z]+/g,
            dt = this;
        return fmtStr.replace(code, function (match) {
            let _weeks = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                _fullweeks = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                _fullmonths = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
                _week_cn = ['日', '一', '二', '三', '四', '五', '六'];
            function _double(num) {
                return num < 10 ? '0' + num : num.toString()
            }
            switch (match) {
                case 'yyyy':
                    return dt.getFullYear().toString();
                case 'yy':
                    return dt.getFullYear().toString().slice(-2);
                case 'mm':
                    return _double(dt.getMonth() + 1);
                case 'm':
                    return (dt.getMonth() + 1).toString();
                case 'dd':
                    return _double(dt.getDate());
                case 'd':
                    return dt.getDate().toString();
                case 'HH':
                    return _double(dt.getHours());
                case 'H':
                    return dt.getHours().toString();
                case 'MM':
                    return _double(dt.getMinutes());
                case 'M':
                    return dt.getMinutes().toString();
                case 'SS':
                    return _double(dt.getSeconds());
                case 'S':
                    return dt.getSeconds().toString();
                case 'II':
                    return _double(dt.getHours() % 12);
                case 'I':
                    return (dt.getHours() % 12).toString();
                case 'p':
                    return dt.getHours() >= 12 ? 'pm' : 'am';
                case 'P':
                    return dt.getHours() >= 12 ? 'Pm' : 'Am';
                case 'a':
                    return _weeks[dt.getDay()];
                case 'A':
                    return _fullweeks[dt.getDay()];
                case 'ac':
                    return _week_cn[dt.getDay()];
                case 'b':
                    return _months[dt.getMonth()];
                case 'B':
                    return _fullmonths[dt.getMonth()];
                default:
                    return match;
            }
        });
    };
}


// parse query
function parseSearch() {
    let args = {};
    if (! location.search)
        return args
    let ss = location.search.slice(1).split('&');
    let kv;
    for(let i=0; i<ss.length; i++){
        kv = ss[i].split('=');
        if (! kv.length === 2)
            continue
        // encodeURIComponent将空格被编码为%20，解码后是空格。
        // 而jquery.param会把空格编码为+, 解码时得到的是+， 再次编码+号被编码为%2B
        args[kv[0]] = decodeURIComponent(kv[1]).replace(/\+/g, ' ');
    }
    return args;
}


function goPage(idx) {
    let args = parseSearch();
    args.pageindex = idx;
    return location.assign(location.pathname + '?' + $.param(args));
}


// refresh marked with a timestamp appended to url
function refresh() {
    let url = location.pathname,
        t = new Date().getTime();
    if (location.search){
        url += location.search + '&t=' + t;
    }
    else {
        url += '?t=' + t;
    }
    return location.assign(url);
}

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
                $form.find('.uk-form-danger').removeClass('uk-form-danger');
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
                        // $form.find('[name=' + field + ']').addClass('uk-form-danger');
                        $form.find('#' + field).addClass('uk-form-danger');
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
            if (arguments.length===2){
                callback=data;
                data={};
            }
            return this.each(function () {
                let $form = $(this);
                $form.showFormError();
                $form.showFormLoading(true);
                _httpJson('POST', url, data, function (err, data) {
                    if (err){
                        if (! callback){
                            $form.showFormError(err);
                        }
                        $form.showFormLoading(false);
                    }
                    callback && callback(err, data);
                });

            });
        }
    });
});

//ajax
function _httpJson(method, url, data, callback) {
    let opt = {
        url: url,
        data: data,     // encodeURIComponent not needed. ajax will transfer GET-data to str and append it to url automatically.
        dataType: 'json',
        type: method.toUpperCase()
    };
    if(method.toUpperCase() === 'POST'){
        opt.contentType = 'application/json';
        opt.data = JSON.stringify(data);
    }
    $.ajax(url, opt)
        .done(function (data) {
            if (data && data.error){
                return callback(data);
            }
            return callback(null, data);
        })
        .fail(function (jqXHR) {
            return callback({error: 'ajax failed.', data: jqXHR.status.toString(),  msg: jqXHR.statusText});
        });
}

function getJson(url, data, callback) {
    if (arguments.length === 2) {
        callback = data;
        data = {};
    }
    return _httpJson('GET', url, data, callback);
}

function postJson(url, data, callback) {
    if (arguments.length === 2) {
        callback = data;
        data = {};
    }
    return _httpJson('POST', url, data, callback);
}


// vue component
if (typeof Vue !== 'undefined'){
    Vue.component('pagination', {
        props: ['page'],
        data: function () {
            return {
                radius: 2
            }
        },
        template: '<ul v-if="page.pageindex" class="uk-pagination" :page="page">\n' +
        '  <li v-if="page.hasprev"><a href="#" @click="goto(page.pageindex-1)"><i class="uk-icon-angle-double-left"></i></a></li>\n' +
        '  <li v-else class="uk-disabled"><span><i class="uk-icon-angle-double-left"></i></span></li>\n' +
        '  <li v-if="page.hasprev"><a @click="goto(1)">1</a></li>\n' +
        '  <li v-if="page.pageindex > 4"><span>...</span></li>\n' +
        '  <li v-for="p in before(page)"><a @click="goto(p)">{{ p }}</a></li>\n' +
        '  <li class="uk-active"><span>{{ page.pageindex }}</span></li>\n' +
        '  <li v-for="p in after(page)"><a @click="goto(p)">{{ p }}</a></li>\n' +
        '  <li v-if="page.pageindex < page.pagecount - 3"><span>...</span></li>\n' +
        '  <li v-if="page.hasnext"><a @click="goto(page.pagecount)">{{ page.pagecount }}</a></li>\n' +
        '  <li v-if="page.hasnext"><a href="#" @click="goto(page.pageindex+1)"><i class="uk-icon-angle-double-right"></i></a></li>\n' +
        '  <li v-else class="uk-disabled"><span><i class="uk-icon-angle-double-right"></i></span></li>\n' +
        '</ul>',
        methods: {
            goto: function (pageidx) {
                return goPage(pageidx);
            },
            before: function (page) {
                console.log('before, ' + page)
                let idx = page.pageindex,
                    pages = [];
                for (let i=0; i<this.radius; i++){
                    idx -= 1;
                    if (idx <= 1)
                        break;
                    pages.unshift(idx);
                }
                return pages;
            },
            after: function (page) {
                let idx = page.pageindex,
                    maxp = page.pagecount,
                    pages = [];
                for (let i=0; i<this.radius; i++){
                    idx += 1;
                    if (idx >= maxp)
                        break;
                    pages.push(idx);
                }
                return pages
            }
        }
    });
}


// display error info in manage pages.
function _displayError($obj, err) {
    $obj.filter(':visible').hide();
    let msg = err && err.msg || String(err),
        code = err && err.error || '500',
        htmls = [];
    htmls.push('<div class="uk-alert uk-alert-danger"' + '>');
    htmls.push('<p>Error: ' + msg + '</p>');
    htmls.push('<p>Code: ' + code + '</p>');
    htmls.push('</div>');
    $obj.html(htmls.join('\n')).slideDown();
}

function showError(err) {
    return _displayError($('#error'), err)
}

function showFatal(err) {
    return _displayError($('#loading'), err)
}