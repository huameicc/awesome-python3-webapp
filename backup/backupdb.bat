@rem backup mysql database awesome to awesome_back_<yyyymmdd>.sql or awesome_back_<yyyymmdd>_<N>.sql

@echo off
@rem utf8 65001 gbk 936 en_us 437
@chcp 65001
@cls


@rem gbk yyyy-mm-dd week
@rem set var_date=%date:~0,4%%date:~5,2%%date:~8,2%
@rem utf8 week yyyy-mm-dd
set var_date=%date:~-10,-6%%date:~-5,-3%%date:~-2%

set var_file=awesome_back_%var_date%.sql
set /a _i=1

echo.
echo ----------------------------------------------
echo 备份 mysql 数据库 awesome...
echo.
if not exist %var_file% goto end

:query
	set _q=Y
	set /p _q=%var_file%已经存在，是否覆盖 Y/N ? (默认值Y) 
	set /p=%_q% <nul
	if %_q% == Y goto end
	if %_q% == y goto end
	if %_q% == N goto while
	if %_q% == n goto while
	echo 无法识别输入命令.
	goto query

:while

@rem echo.
@rem echo while: %var_file%
@rem echo while: %_i%
@rem echo.

if exist %var_file% (	
	set /a _i=%_i%+1
	set var_file=awesome_back_%var_date%_%_i%.sql
	goto while
)

:end

@rem set /p= 将使用文件名: %var_file% <nul
echo 将使用文件名: %var_file%
echo.

set var_cmd=mysqldump -u root -p awesome -r %var_file%
echo %var_cmd%

%var_cmd%
echo.

@rem empty?
set _bytesize=0
set _file="%var_file%"

FOR /F "usebackq" %%A IN ('%_file%') do set _size=%%~zA

if %_size% LEQ %_bytesize% (
	echo 生成文件为空, 删除 %var_file%
	DEL %_file%
) else (
	echo 备份成功: %var_file%, bytesize: %_size%
) 

echo ----------------------------------------------
echo.
@pause
