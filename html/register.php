<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"> 
<html>
<head>
<?php
	require('../include/header.php');
?>

<script type="text/javascript">
$(function(){
        console.log('clicked');
		var icon_cdn =$('#icon_cdn').attr('value');
		$("#next").live('click',function(){
			$.getJSON("ajax/write.php",{action:'stepup'},function(data){
				window.location = '/profile.php?hl=bio';
			});
		});
		
		$('#ppform').ajaxForm(function() {});  
		$('#profile_photo_upload_button').click(function()
		{
		  console.log('clicked');
			$("#photo_preview").html('<img src="'+icon_cdn+'/upload.gif" alt="Uploading...."/>');
			$("#ppform").ajaxSubmit(
			{
				type:'post',
				success: function(response){ 
				var data = $.parseJSON(response);
					if(data.ack == '1')
					{					
						$('#main_div').html('<img src ="'+data.thumb+'" style="max-width:33.5em;margin-bottom:1em;cursor:pointer;border:0.1em solid #aaaaaa;" data="'+data.thumb+'" class="viewable" id="'+data.actionid+' " />');
					}
					else if(data.ack == '2')
					{
						$('#photo_preview').html('Unable to upload image. Please try again.');
					}
					else if(data.ack == '3')
					{
						$('#photo_preview').html('Image size is more than 10Mb. Please compress this image and try again.');
					}
					else if(data.ack == '4')
					{
						$('#photo_preview').html('Please upload an image of jpg/jpeg, png, gif, bmp type only. Please change the image type and try again.');
					}
					else if(data.ack == '5')
					{
						$('#photo_preview').html('Please chose a photo to upload');
					}						
				}
			});
			return false;
		}); 
	});	
	
	function chooseFile() 
	{
		$("#photo_box").click();
	}
</script>
</head>
<body>
<div class="container-fluid">
  <div class="row" >
  <div class="col-md-10">
    <div class="row home_row left1">
	<div class="col-xs-6 col-md-2 " id="left"></div>
	<div id="center" class="col-md-6 center top7">
 <div class="panel panel-default">
	<?php 
		if($page == 'friend_suggest')
		{
	?>
    
<div class="panel-heading"><h4 class=""><?php echo $_SESSION['NAME']; ?>, Please follow some people on your network </h4>
</div>

	<div id="friend_suggest" class="panel-body"></div>
	<?php
		}
		else if($page == 'group_suggest')
		{
	?>
<div class="panel-heading"><h4 class=""><?php echo $_SESSION['NAME']; ?>, Groups you can join </h4></div>
	<div id="group_suggest" class="panel-body"></div>
	<?php
		}
		else if($page == 'profile_picture')
		{
			?>
<div class="panel-heading"><h4 class=""><?php echo $_SESSION['NAME']; ?>, let's upload a profile picture</h4></div>
			<div id="main_div" style="text-align:center;margin-top:4em;" class="panel-body">
			<div id="photo_preview" style="text-align:center;margin:0em 0em 1em 0em;"></div>	
			
					<form id="ppform" method="post" enctype="multipart/form-data" action="/ajax/write.php">
						<div style="">
							<input type="file" id="photo_box" name="photo_box" class="file_inline"/>
						<button type="button" id="profile_photo_upload_button" class="theme_button">Upload</button>
						</div>
						<input type="hidden" name="action" value="profile_picture_upload"/>
					</form>
			</div>
			<?php
		}
	?>
	<span id="next" style="font-weight:bold;position:absolute;top:2em;right:2em;cursor:pointer;">Skip</span>
    </div>
	</div>
</div>
</div>
<div class="col-md-2">
<input type="hidden" id="step_hidden" value="<?php echo $_SESSION['STEP']; ?>"/>
<?php require_once('../include/footer.php'); ?>
</div>
</div>
</div>
</body>
</html>